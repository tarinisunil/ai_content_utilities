import logging

logger = logging.getLogger(__name__)


def build_sections(blocks):
    sections = []
    current = None

    for block in blocks:
        btype = block.get("type")
        text = block.get("text", "").strip()

        if not text:
            continue

        # --- Start new section ---
        if btype == "heading":
            current = {
                "heading": text,
                "content": []  # unified content stream
            }
            sections.append(current)

        # --- Before first heading ---
        elif current is None:
            current = {
                "heading": "Introduction",
                "content": []
            }
            sections.append(current)

            current["content"].append({
                "type": btype,
                "text": text
            })

        # --- Add content to section ---
        else:
            current["content"].append({
                "type": btype,
                "text": text
            })

    logger.info("build_sections: built %d sections", len(sections))
    return sections