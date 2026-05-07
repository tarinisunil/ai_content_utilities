import json
import tempfile
from typing import Any, Dict, List
import time
import traceback
import logging
import pandas as pd
import streamlit as st

from extractor import extract_blocks
from structure import build_sections, flatten_sections, render_section_tree
from chunker import chunk_sections
from utils import build_prompt, extract_json
from llm import generate_json
from merger import merge_results
from scorer import compute_confidence
from finalizer import finalize_document, apply_final_metadata

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Document Intelligence",
    layout="wide",
)

st.title("📄 Hierarchical Document Intelligence Pipeline")


def safe_generate(prompt: str, retries: int = 3) -> Any:
    last_err = None

    for attempt in range(retries):
        try:
            logger.info("LLM attempt %d/%d", attempt + 1, retries)
            raw = generate_json(prompt)
            logger.info("LLM raw output length: %d", len(raw or ""))
            return extract_json(raw)
        except Exception as e:
            last_err = e
            logger.exception("LLM attempt %d failed", attempt + 1)

    raise RuntimeError("LLM failed after retries") from last_err


def process_chunks(chunks: List[List[Dict[str, Any]]]) -> List[Any]:
    results = []
    for i, chunk in enumerate(chunks):
        logger.info("Processing chunk %d/%d", i + 1, len(chunks))
        logger.info("Chunk %d has %d sections", i + 1, len(chunk))

        prompt = build_prompt(chunk)
        logger.info("Chunk %d prompt length: %d", i + 1, len(prompt))

        parsed = safe_generate(prompt)
        results.append(parsed)

    return results


def collect_sections_recursive(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Return a flat list of all sections, including nested children if present.
    """
    flat = []

    def walk(items: List[Dict[str, Any]]) -> None:
        for sec in items or []:
            if not isinstance(sec, dict):
                continue
            flat.append(sec)
            children = sec.get("children", [])
            if isinstance(children, list) and children:
                walk(children)

    walk(sections)
    return flat


def section_path(sec: Dict[str, Any]) -> str:
    path = sec.get("path") or []
    if isinstance(path, list) and path:
        return " > ".join(str(p) for p in path if str(p).strip())
    return sec.get("heading", "") or "(untitled)"


def section_level(sec: Dict[str, Any]) -> int:
    try:
        return int(sec.get("level", 1) or 1)
    except Exception:
        return 1


def section_confidence(sec: Dict[str, Any]) -> float:
    conf = sec.get("confidence", 0.0)
    if isinstance(conf, (int, float)):
        return float(conf)
    return 0.0


def count_content_items(sec: Dict[str, Any]) -> int:
    content = sec.get("content", [])
    return len(content) if isinstance(content, list) else 0


def build_section_table(sections: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for idx, sec in enumerate(collect_sections_recursive(sections), start=1):
        kws = sec.get("keywords", [])
        if not isinstance(kws, list):
            kws = []

        notes = sec.get("notes", [])
        if not isinstance(notes, list):
            notes = []

        rows.append(
            {
                "#": idx,
                "path": section_path(sec),
                "heading": sec.get("heading", ""),
                "level": section_level(sec),
                "type": sec.get("type", "general"),
                "confidence": round(section_confidence(sec), 2),
                "keywords": len(kws),
                "content_items": count_content_items(sec),
                "notes": len(notes),
            }
        )

    return pd.DataFrame(rows)


def detect_failures(final_output: Dict[str, Any], section_df: pd.DataFrame) -> List[str]:
    issues = []

    title = (final_output.get("title") or "").strip()
    summary = (final_output.get("summary") or "").strip()
    doc_type = (final_output.get("document_type") or "unknown").strip().lower()
    overall_conf = float(final_output.get("confidence", 0.0) or 0.0)

    if not title:
        issues.append("No title was detected.")
    if not summary:
        issues.append("No document summary was produced.")
    if doc_type in {"unknown", ""}:
        issues.append("Document type is still unknown.")

    if overall_conf < 0.6:
        issues.append(f"Overall confidence is low ({overall_conf:.2f}).")

    if section_df.empty:
        issues.append("No sections were extracted.")
        return issues

    if section_df["confidence"].mean() < 0.6:
        issues.append("Average section confidence is weak.")

    low_conf_sections = section_df[section_df["confidence"] < 0.55]
    if len(low_conf_sections) >= max(2, len(section_df) // 3):
        issues.append("A significant portion of sections have low confidence.")

    if section_df["keywords"].sum() == 0:
        issues.append("No keywords were extracted for any section.")

    if section_df["level"].max() <= 1 and len(section_df) > 2:
        issues.append("The document looks too flat; hierarchy reconstruction may be weak.")

    dup_paths = section_df["path"].duplicated().sum()
    if dup_paths > 0:
        issues.append("Some section paths appear duplicated.")

    repeated_headings = section_df["heading"].duplicated().sum()
    if repeated_headings > 0:
        issues.append("Repeated headings were detected.")

    return issues


def confidence_bucket(conf: float) -> str:
    if conf >= 0.8:
        return "High"
    if conf >= 0.6:
        return "Medium"
    return "Low"


def render_confidence_heatmap(section_df: pd.DataFrame) -> None:
    if section_df.empty:
        st.info("No sections available for heatmap.")
        return

    heat_df = section_df.copy()
    heat_df["confidence_bucket"] = heat_df["confidence"].apply(confidence_bucket)

    styled = (
        heat_df[["path", "heading", "level", "type", "confidence", "confidence_bucket", "keywords", "notes"]]
        .style
        .background_gradient(subset=["confidence"], cmap="YlOrRd")
        .format({"confidence": "{:.2f}"})
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

def run_step(name, fn):
    start = time.perf_counter()
    logger.info("%s started", name)
    st.write(f"Running: {name}...")

    try:
        result = fn()
        elapsed = time.perf_counter() - start
        logger.info("%s finished in %.2fs", name, elapsed)
        st.write(f"Done: {name} ({elapsed:.2f}s)")
        return result
    except Exception as e:
        elapsed = time.perf_counter() - start
        logger.exception("%s failed after %.2fs", name, elapsed)
        st.error(f"{name} failed after {elapsed:.2f}s")
        st.code(traceback.format_exc())
        raise

def render_section_content(section: Dict[str, Any]) -> None:
    """
    Render paragraphs, bullets, and tables for the selected section.
    """
    content = section.get("content", [])
    if not isinstance(content, list) or not content:
        st.info("This section has no content.")
        return

    st.write("### Section Content")

    for item in content:
        if not isinstance(item, dict):
            st.write(str(item))
            continue

        item_type = item.get("type", "paragraph")

        if item_type == "paragraph":
            text = (item.get("text") or "").strip()
            if text:
                st.markdown(text)

        elif item_type == "bullet":
            text = (item.get("text") or "").strip()
            if text:
                st.markdown(f"- {text}")

        elif item_type == "table":
            st.markdown("#### Table")
            rows = item.get("rows", [])

            if isinstance(rows, list) and rows:
                try:
                    headers = rows[0] if isinstance(rows[0], list) else []
                    data = rows[1:] if len(rows) > 1 else []

                    if headers and data:
                        width = len(headers)
                        normalized_rows = []
                        for row in data:
                            if not isinstance(row, list):
                                row = [str(row)]
                            row = [str(cell) for cell in row]
                            if len(row) < width:
                                row = row + [""] * (width - len(row))
                            elif len(row) > width:
                                row = row[:width]
                            normalized_rows.append(row)

                        df = pd.DataFrame(normalized_rows, columns=headers)
                        st.table(df)
                    else:
                        st.write(rows)
                except Exception:
                    st.write(rows)
            else:
                st.write(item.get("text", ""))

        else:
            st.write(item)

    st.write("### Full Section JSON")
    st.json(section)


uploaded = st.file_uploader("Upload DOCX", type=["docx"])

if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(uploaded.read())
        docx_path = tmp.name

    st.info("Running pipeline...")

    # Step 1
    blocks = run_step("extract_blocks", lambda: extract_blocks(docx_path))


    # Step 2
    sections_tree = run_step("build_sections", lambda: build_sections(blocks))


    # Step 3
    flat_sections = run_step("flatten_sections", lambda: flatten_sections(sections_tree))

    chunks = run_step("chunk_sections", lambda: chunk_sections(flat_sections))


    # Step 4
    results = run_step("process_chunks", lambda: process_chunks(chunks))


    # Step 5
    final_output = run_step("merge_results", lambda: merge_results(results))


    # Step 6
    original_text = " ".join(b.get("text", "") for b in blocks)
    final_output["confidence"] = run_step(
    "compute_confidence",
    lambda: compute_confidence(final_output["sections"], original_text),
)


    # Step 7
    metadata = run_step("finalize_document", lambda: finalize_document(final_output))
    final_output = apply_final_metadata(final_output, metadata)

    section_df = build_section_table(final_output.get("sections", []))
    issues = detect_failures(final_output, section_df)

    # =========================
    # Top summary
    # =========================
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Confidence", f"{final_output.get('confidence', 0.0):.2f}")
    c2.metric("Section count", f"{len(section_df)}")
    c3.metric("Doc type", final_output.get("document_type", "unknown"))
    c4.metric("Keywords", f"{len(final_output.get('keywords', []))}")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("📚 Document Summary")
        st.markdown(f"**Title:** {final_output.get('title', '')}")
        st.markdown(f"**Type:** {final_output.get('document_type', 'unknown')}")
        st.markdown(f"**Confidence:** {final_output.get('confidence', 0.0):.2f}")
        st.markdown("**Summary:**")
        st.write(final_output.get("summary", ""))
        st.markdown("**Keywords:**")
        st.write(final_output.get("keywords", []))

    with right:
        st.subheader("🌳 Section Tree")
        st.code(render_section_tree(sections_tree), language="text")

    st.divider()

    # =========================
    # Section Explorer
    # =========================
    st.subheader("🧭 Section Explorer")

    if section_df.empty:
        st.info("No sections to explore.")
    else:
        options = list(range(len(section_df)))
        labels = [
            f"{row['path']}  |  {row['type']}  |  conf {row['confidence']:.2f}"
            for _, row in section_df.iterrows()
        ]

        selected_idx = st.selectbox(
            "Choose a section",
            options=options,
            format_func=lambda i: labels[i],
        )

        selected = section_df.iloc[selected_idx].to_dict()

        col_a, col_b = st.columns([1, 1])

        with col_a:
            st.markdown(f"**Path:** {selected['path']}")
            st.markdown(f"**Heading:** {selected['heading']}")
            st.markdown(f"**Level:** {selected['level']}")
            st.markdown(f"**Type:** {selected['type']}")
            st.markdown(f"**Confidence:** {selected['confidence']:.2f}")
            st.markdown(f"**Keywords:** {int(selected['keywords'])}")
            st.markdown(f"**Notes:** {int(selected['notes'])}")
            st.markdown(f"**Content items:** {int(selected['content_items'])}")

        with col_b:
            matched = next(
                (
                    sec
                    for sec in collect_sections_recursive(final_output.get("sections", []))
                    if section_path(sec) == selected["path"]
                ),
                None,
            )

            if matched:
                render_section_content(matched)
            else:
                st.info("Detailed section object not found.")

    st.divider()

    # =========================
    # Confidence Heatmap
    # =========================
    st.subheader("🔥 Confidence Heatmap")
    render_confidence_heatmap(section_df)

    st.divider()

    # =========================
    # Failure Visualization
    # =========================
    st.subheader("⚠️ Failure Visualization")

    if issues:
        st.error("The pipeline detected possible weak spots in this document.")
        for issue in issues:
            st.write(f"• {issue}")
    else:
        st.success("No major failure signals detected.")

    with st.expander("Show detailed failure signals"):
        st.write("### Low-confidence sections")
        if section_df.empty:
            st.write("No section data.")
        else:
            low_df = section_df[section_df["confidence"] < 0.55]
            if low_df.empty:
                st.write("None")
            else:
                st.dataframe(
                    low_df[["path", "heading", "type", "confidence", "keywords", "notes"]],
                    use_container_width=True,
                    hide_index=True,
                )

        st.write("### Raw output")
        st.json(final_output)

    st.divider()

    st.subheader("🧾 Structured JSON")
    st.json(final_output)
