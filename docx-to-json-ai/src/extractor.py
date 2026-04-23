import logging

from docx import Document

logger = logging.getLogger(__name__)


def extract_text(docx_path):
    logger.info("extract_text: opening document path=%s", docx_path)
    doc = Document(docx_path)
    total_paras = len(doc.paragraphs)
    logger.debug("extract_text: total paragraphs in document=%d", total_paras)

    text = []
    skipped_empty = 0
    for para in doc.paragraphs:
        stripped = para.text.strip()
        if stripped:
            text.append(stripped)
        else:
            skipped_empty += 1

    joined = "\n".join(text)
    logger.info(
        "extract_text: kept %d non-empty paragraphs, skipped %d empty, output length=%d chars",
        len(text),
        skipped_empty,
        len(joined),
    )
    return joined