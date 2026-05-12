import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


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

        # Oversized section: isolate it in its own chunk
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

        # Start a new chunk if needed
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


def chunk_naive_blocks(blocks: List[Dict[str, Any]], max_chars: int = 1500) -> List[List[Dict[str, Any]]]:
    """
    Group raw document blocks into chunks by character count, ignoring structure.
    Used as the naive baseline for retrieval comparison.
    """
    chunks: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    current_size = 0

    for block in blocks:
        size = len(block.get("text", "") or "")
        if current and current_size + size > max_chars:
            chunks.append(current)
            current, current_size = [], 0
        current.append(block)
        current_size += size

    if current:
        chunks.append(current)

    logger.info("chunk_naive_blocks: created %d chunks", len(chunks))
    return chunks


def _item_char_size(item: Dict[str, Any]) -> int:
    """Character size of any item — works for both raw blocks and sections."""
    if "content" in item or "path" in item:
        return section_size(item)
    return len(item.get("text", "") or "")


def chunk_stats(chunks: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Return summary statistics for a list of chunks (naive or hierarchical)."""
    if not chunks:
        return {"count": 0, "avg_size": 0, "min_size": 0, "max_size": 0}
    sizes = [sum(_item_char_size(item) for item in chunk) for chunk in chunks]
    return {
        "count": len(chunks),
        "avg_size": int(sum(sizes) / len(sizes)),
        "min_size": min(sizes),
        "max_size": max(sizes),
    }


def chunk_to_text(chunk: List[Dict[str, Any]]) -> str:
    """
    Optional helper for debugging or logging.
    Converts a chunk into readable text with section metadata.
    """
    lines: List[str] = []

    for i, sec in enumerate(chunk, start=1):
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
