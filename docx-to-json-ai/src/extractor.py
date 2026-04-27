import logging
from docx import Document

logger = logging.getLogger(__name__)


def extract_blocks(docx_path):
    logger.info("extract_blocks: opening document path=%s", docx_path)
    doc = Document(docx_path)

    blocks = []
    skipped_empty = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        style = para.style.name if para.style else ""

        if not text:
            skipped_empty += 1
            continue

        # --- Heading detection ---
        if style.startswith("Heading"):
            try:
                level = int(style.split(" ")[1])
            except (IndexError, ValueError):
                level = 1  # fallback

            blocks.append({
                "type": "heading",
                "text": text,
                "level": level
            })

        # --- Bullet / list detection ---
        elif "List" in style or "Bullet" in style:
            blocks.append({
                "type": "bullet",
                "text": text
            })

        # --- Default paragraph ---
        else:
            blocks.append({
                "type": "paragraph",
                "text": text
            })

    logger.info(
        "extract_blocks: created %d blocks, skipped %d empty paragraphs",
        len(blocks),
        skipped_empty
    )

    return blocks