import logging

logger = logging.getLogger(__name__)


def section_to_text(sec):
    """
    Convert a section into plain text for size estimation.
    """
    parts = []

    # Add heading
    if sec.get("heading"):
        parts.append(sec["heading"])

    # Add content
    for item in sec.get("content", []):
        if isinstance(item, dict):
            parts.append(item.get("text", ""))
        else:
            parts.append(str(item))

    return " ".join(parts)


def chunk_sections(sections, max_chars=1500):
    chunks = []
    current_chunk = []
    current_size = 0

    for sec in sections:
        sec_text = section_to_text(sec)
        sec_len = len(sec_text)

        # --- Handle oversized section ---
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

        # --- Check if adding exceeds limit ---
        if current_size + sec_len > max_chars:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0

        # --- Add section ---
        current_chunk.append(sec)
        current_size += sec_len

    # --- (last chunk) ---
    if current_chunk:
        chunks.append(current_chunk)

    logger.info("chunk_sections: created %d chunks", len(chunks))
    return chunks