import json
import logging
import tempfile
import time
import traceback
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from chunker import chunk_naive_blocks, chunk_sections, chunk_stats, _item_char_size
from extractor import extract_blocks
from finalizer import apply_final_metadata, finalize_document
import llm as llm_module
from llm import generate_json
from merger import merge_results
from scorer import compute_confidence
from retrieval import retrieve
from structure import build_sections, flatten_sections, render_section_tree
from utils import build_prompt, extract_json


logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Document Intelligence",
    layout="wide",
)

st.title("📄 Hierarchical Document Intelligence Pipeline")

# --- Sidebar: LLM provider selection ---
with st.sidebar:
    st.header("LLM Provider")
    provider = st.radio("Provider", ["openrouter", "ollama"], index=0)
    default_model = "llama3.2" if provider == "ollama" else "openai/gpt-oss-20b:free"
    model = st.text_input("Model", value=default_model)
    llm_module.configure_provider(provider, model or None)
    st.caption(f"Active model: `{llm_module.MODEL_ID}`")


def run_step(name: str, fn):
    """
    Run a pipeline step with timing + Streamlit logging.
    """
    start = time.perf_counter()
    logger.info("%s started", name)
    st.write(f"Running: {name}...")

    try:
        result = fn()
        elapsed = time.perf_counter() - start
        logger.info("%s finished in %.2fs", name, elapsed)
        st.write(f"Done: {name} ({elapsed:.2f}s)")
        return result
    except Exception:
        elapsed = time.perf_counter() - start
        logger.exception("%s failed after %.2fs", name, elapsed)
        st.error(f"{name} failed after {elapsed:.2f}s")
        st.code(traceback.format_exc())
        raise


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
    Return a flat list of all sections in preorder, including nested children.
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


def render_chunk_item(item: Dict[str, Any]) -> str:
    """Return a one-line preview string for any chunk item (raw block or section)."""
    path = item.get("path")
    if path and isinstance(path, list) and path:
        return f"[{' > '.join(str(p) for p in path)}]"
    heading = (item.get("heading") or "").strip()
    if heading:
        return f"[{heading}]"
    item_type = item.get("type", "block")
    text = (item.get("text", "") or "").strip()
    preview = (text[:80] + "…") if len(text) > 80 else text
    return f"({item_type}) {preview}"


def build_section_table(sections: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Build a flat table view of all sections.

    section_idx is the stable index used to retrieve the exact section in the
    explorer, avoiding path-based collisions.
    """
    rows = []
    flat_sections = collect_sections_recursive(sections)

    for idx, sec in enumerate(flat_sections):
        kws = sec.get("keywords", [])
        if not isinstance(kws, list):
            kws = []

        notes = sec.get("notes", [])
        if not isinstance(notes, list):
            notes = []

        path = section_path(sec)
        sec_type = sec.get("type", "general")
        conf = round(section_confidence(sec), 2)

        rows.append(
            {
                "section_idx": idx,
                "display": f"[{idx}] {path} | {sec_type} | conf {conf:.2f}",
                "path": path,
                "heading": sec.get("heading", ""),
                "level": section_level(sec),
                "type": sec_type,
                "confidence": conf,
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


def confidence_bar(conf: float, width: int = 10) -> str:
    filled = max(0, min(width, int(round(conf * width))))
    return "█" * filled + "░" * (width - filled)


def render_confidence_overview(section_df: pd.DataFrame) -> None:
    if section_df.empty:
        st.info("No sections available for confidence overview.")
        return

    view_df = section_df.copy()
    view_df["bucket"] = view_df["confidence"].apply(confidence_bucket)
    view_df["bar"] = view_df["confidence"].apply(confidence_bar)

    st.dataframe(
        view_df[
            [
                "display",
                "level",
                "type",
                "confidence",
                "bucket",
                "bar",
                "keywords",
                "notes",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_section_content(section: Dict[str, Any]) -> None:
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

    blocks = run_step("extract_blocks", lambda: extract_blocks(docx_path))
    sections_tree = run_step("build_sections", lambda: build_sections(blocks))
    flat_sections = run_step("flatten_sections", lambda: flatten_sections(sections_tree))
    chunks = run_step("chunk_sections", lambda: chunk_sections(flat_sections))
    naive_chunks = chunk_naive_blocks(blocks)
    results = run_step("process_chunks", lambda: process_chunks(chunks))
    final_output = run_step("merge_results", lambda: merge_results(results))

    original_text = " ".join(b.get("text", "") for b in blocks)
    final_output["confidence"] = run_step(
        "compute_confidence",
        lambda: compute_confidence(final_output["sections"], original_text),
    )

    metadata = run_step("finalize_document", lambda: finalize_document(final_output))
    final_output = apply_final_metadata(final_output, metadata)

    section_df = build_section_table(final_output.get("sections", []))
    issues = detect_failures(final_output, section_df)
    flat_sections = collect_sections_recursive(final_output.get("sections", []))

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

    # ── Chunking Comparison ────────────────────────────────────────────────────
    st.subheader("📦 Chunking Comparison")

    naive_s = chunk_stats(naive_chunks)
    hier_s = chunk_stats(chunks)

    ms1, ms2, ms3, ms4, ms5, ms6 = st.columns(6)
    ms1.metric("Naive chunks", naive_s["count"])
    ms2.metric("Naive avg chars", naive_s["avg_size"])
    ms3.metric("Hier chunks", hier_s["count"])
    ms4.metric("Hier avg chars", hier_s["avg_size"])
    ms5.metric("Confidence", f"{final_output.get('confidence', 0.0):.2f}")
    ms6.metric("Sections", len(section_df))

    chunk_mode = st.radio(
        "View mode",
        ["Both", "Naive only", "Hierarchical only"],
        horizontal=True,
        key="chunk_mode",
    )

    def _render_chunk_cards(chunk_list: List[List[Dict[str, Any]]], label: str) -> None:
        stats = chunk_stats(chunk_list)
        st.markdown(f"**{label}**")
        st.caption(
            f"{stats['count']} chunks · avg {stats['avg_size']} chars "
            f"· min {stats['min_size']} · max {stats['max_size']}"
        )
        for i, chunk in enumerate(chunk_list):
            size = sum(_item_char_size(item) for item in chunk)
            with st.expander(f"Chunk {i + 1} — {size} chars — {len(chunk)} items"):
                for item in chunk:
                    st.text(render_chunk_item(item))

    if chunk_mode == "Both":
        col_n, col_h = st.columns(2)
        with col_n:
            _render_chunk_cards(naive_chunks, "Naive Chunks")
        with col_h:
            _render_chunk_cards(chunks, "Hierarchical Chunks")
    elif chunk_mode == "Naive only":
        _render_chunk_cards(naive_chunks, "Naive Chunks")
    else:
        _render_chunk_cards(chunks, "Hierarchical Chunks")

    st.divider()

    st.subheader("🧭 Section Explorer")

    if section_df.empty:
        st.info("No sections to explore.")
    else:
        selected_display = st.selectbox(
            "Choose a section",
            options=section_df["display"].tolist(),
            key="section_explorer",
        )

        selected_row = section_df[section_df["display"] == selected_display].iloc[0]
        selected = selected_row.to_dict()
        matched = flat_sections[int(selected["section_idx"])]

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
            render_section_content(matched)

    st.divider()

    st.subheader("🔥 Confidence Overview")
    render_confidence_overview(section_df)

    st.divider()

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
                    low_df[["display", "heading", "type", "confidence", "keywords", "notes"]],
                    use_container_width=True,
                    hide_index=True,
                )

        st.write("### Raw output")
        st.json(final_output)

    st.divider()

    st.subheader("🧾 Structured JSON")
    st.json(final_output)

    st.divider()

    st.subheader("🔍 Retrieval Simulator — Naive vs Hierarchical")
    st.caption("Keyword-overlap retrieval. No embeddings. Shows why structure matters.")

    _DEMO_QUESTIONS = [
        "What were the risks?",
        "What is the conclusion?",
        "What does the revenue section say?",
    ]

    btn_cols = st.columns(len(_DEMO_QUESTIONS))
    for col, demo_q in zip(btn_cols, _DEMO_QUESTIONS):
        if col.button(demo_q, key=f"demo_{demo_q}"):
            st.session_state["retrieval_question"] = demo_q

    retrieval_question = st.text_input(
        "Or type your own question",
        value=st.session_state.get("retrieval_question", ""),
        key="retrieval_question_input",
    )

    if retrieval_question.strip():
        naive_results = retrieve(retrieval_question, naive_chunks, mode="naive", top_k=1)
        hier_results = retrieve(retrieval_question, chunks, mode="hierarchical", top_k=1)

        col_naive, col_hier = st.columns(2)

        with col_naive:
            st.markdown("### Naive Retrieval")
            if naive_results:
                r = naive_results[0]
                st.metric("Score", r["score"])
                st.markdown(f"**Matched terms:** {', '.join(r['matched_terms']) or 'none'}")
                st.markdown(f"**Context preserved:** {'✅' if r['preserves_context'] else '❌'}")
                st.info(r["why"])
                with st.expander("Chunk preview"):
                    st.text(r["preview"])
            else:
                st.write("No chunks to search.")

        with col_hier:
            st.markdown("### Hierarchical Retrieval")
            if hier_results:
                r = hier_results[0]
                st.metric("Score", r["score"])
                st.markdown(f"**Matched terms:** {', '.join(r['matched_terms']) or 'none'}")
                st.markdown(f"**Context preserved:** {'✅' if r['preserves_context'] else '❌'}")
                st.success(r["why"])
                with st.expander("Chunk preview"):
                    st.text(r["preview"])
            else:
                st.write("No chunks to search.")