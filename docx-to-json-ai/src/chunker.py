from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def block_to_text(block: Dict[str, Any]) -> str:
    """
    Convert a raw extracted block to readable text.
    This is used by the naive chunker, which intentionally ignores structure.
    """
    if not isinstance(block, dict):
        return str(block).strip()

    block_type = block.get("type", "block")
    text = (block.get("text") or "").strip()

    if block_type == "table" and not text:
        rows = block.get("rows", [])
        if rows:
            rendered_rows = []
            for row in rows:
                if isinstance(row, list):
                    rendered_rows.append(" | ".join(str(cell).strip() for cell in row))
            text = "\n".join(rendered_rows).strip()

    return text


def document_to_text(blocks: List[Dict[str, Any]]) -> str:
    """
    Flatten all blocks into plain text.
    Naive chunking should operate on raw text windows, not on structural units.
    """
    parts: List[str] = []

    for block in blocks:
        text = block_to_text(block)
        if text:
            parts.append(text)

    return "\n".join(parts).strip()


def section_to_text(sec: Dict[str, Any]) -> str:
    parts: List[str] = []

    path = sec.get("path") or []
    if path:
        parts.append(" > ".join(path))

    heading = sec.get("heading", "")
    if heading and (not path or path[-1] != heading):
        parts.append(heading)

    for item in sec.get("content", []):
        if not isinstance(item, dict):
            text = str(item).strip()
            if text:
                parts.append(text)
            continue

        item_type = item.get("type", "paragraph")

        if item_type == "table":
            rows = item.get("rows", [])
            if rows:
                rendered_rows = []
                for row in rows:
                    if isinstance(row, list):
                        rendered_rows.append(" | ".join(str(cell).strip() for cell in row))
                table_text = "\n".join(rendered_rows).strip()
                if table_text:
                    parts.append("[TABLE]")
                    parts.append(table_text)
            else:
                text = (item.get("text") or "").strip()
                if text:
                    parts.append("[TABLE]")
                    parts.append(text)
        else:
            text = (item.get("text") or "").strip()
            if text:
                parts.append(text)

    return "\n".join(parts).strip()


def item_to_text(item: Dict[str, Any]) -> str:
    """
    Convert either a raw block, a naive chunk item, or a hierarchical section
    into plain text.
    """
    if not isinstance(item, dict):
        return str(item).strip()

    if item.get("type") == "naive_chunk":
        return (item.get("text") or "").strip()

    if "content" in item or "path" in item:
        return section_to_text(item)

    return block_to_text(item)


def section_size(sec: Dict[str, Any]) -> int:
    """
    Return approximate size of a section in characters.
    """
    return len(section_to_text(sec))


def chunk_sections(sections: List[Dict[str, Any]], max_chars: int = 1500) -> List[List[Dict[str, Any]]]:
    """
    Group flattened sections into chunks without splitting a section.

    Rules:
    - Keep each section intact.
    - Start a new chunk when adding the next section would exceed max_chars.
    - If one section is larger than max_chars, put it alone in a chunk.
    """
    chunks: List[List[Dict[str, Any]]] = []
    current_chunk: List[Dict[str, Any]] = []
    current_size = 0

    for sec in sections:
        sec_len = section_size(sec)

        if sec_len > max_chars:
            logger.warning(
                "chunk_sections: section too large (%d chars), forcing single-section chunk",
                sec_len,
            )

            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_size = 0

            chunks.append([sec])
            continue

        if current_chunk and current_size + sec_len > max_chars:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0

        current_chunk.append(sec)
        current_size += sec_len

    if current_chunk:
        chunks.append(current_chunk)

    logger.info("chunk_sections: created %d chunks", len(chunks))
    return chunks


def _window_text_to_chunk(text: str, start: int, end: int) -> Dict[str, Any]:
    """
    Wrap a naive text window in a dict so the UI can render it consistently.
    """
    return {
        "type": "naive_chunk",
        "text": text.strip(),
        "source": "naive_text_window",
        "start_char": start,
        "end_char": end,
    }


def chunk_naive_blocks(blocks: List[Dict[str, Any]], max_chars: int = 1500) -> List[List[Dict[str, Any]]]:
    """
    True naive chunking baseline.

    1. Flatten the entire document into plain text.
    2. Slice that text into fixed-size character windows.
    3. Ignore headings, bullets, tables, and section boundaries.

    This intentionally produces worse context preservation than chunk_sections().
    """
    full_text = document_to_text(blocks)
    if not full_text:
        return []

    chunks: List[List[Dict[str, Any]]] = []

    for start in range(0, len(full_text), max_chars):
        end = min(start + max_chars, len(full_text))
        window = full_text[start:end]
        if window.strip():
            chunks.append([_window_text_to_chunk(window, start, end)])

    logger.info("chunk_naive_blocks: created %d naive text windows", len(chunks))
    return chunks


def chunk_stats(chunks: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Return summary statistics for a list of chunks (naive or hierarchical).
    """
    if not chunks:
        return {
            "chunk_count": 0,
            "count": 0,
            "avg_size": 0.0,
            "min_size": 0,
            "max_size": 0,
            "avg_items": 0.0,
            "largest_chunk_idx": None,
        }

    sizes = [sum(len(item_to_text(item)) for item in chunk) for chunk in chunks]
    item_counts = [len(chunk) for chunk in chunks]
    largest_idx = max(range(len(sizes)), key=lambda idx: sizes[idx])

    avg_size = round(sum(sizes) / len(sizes), 1)
    avg_items = round(sum(item_counts) / len(item_counts), 1)

    return {
        "chunk_count": len(chunks),
        "count": len(chunks),
        "avg_size": avg_size,
        "min_size": min(sizes),
        "max_size": max(sizes),
        "avg_items": avg_items,
        "largest_chunk_idx": largest_idx,
    }


def chunk_to_text(chunk: List[Dict[str, Any]]) -> str:
    """
    Optional helper for debugging or logging.
    Converts a chunk into readable text with section metadata.
    """
    lines: List[str] = []

    for i, sec in enumerate(chunk, start=1):
        if sec.get("type") == "naive_chunk":
            lines.append(f"[Naive Chunk {i}]")
            lines.append((sec.get("text") or "").strip())
            lines.append("")
            continue

        path = sec.get("path") or []
        heading = sec.get("heading", "")
        level = sec.get("level", 1)
        sec_type = sec.get("type", "general")

        lines.append(f"[Section {i}]")
        if path:
            lines.append(f"Path: {' > '.join(path)}")
        else:
            lines.append(f"Heading: {heading}")
        lines.append(f"Level: {level}")
        lines.append(f"Type: {sec_type}")

        for item in sec.get("content", []):
            if isinstance(item, dict):
                text = (item.get("text") or "").strip()
                item_type = item.get("type", "paragraph")
                if text:
                    lines.append(f"- ({item_type}) {text}")
            else:
                text = str(item).strip()
                if text:
                    lines.append(f"- {text}")

        lines.append("")

    return "\n".join(lines).strip()
