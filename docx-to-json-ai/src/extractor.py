import logging
from typing import Any, Dict, Iterable, List

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

logger = logging.getLogger(__name__)


def looks_like_soft_heading(text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False
    if len(text) > 60:
        return False
    if text.endswith("."):
        return False
    return text.istitle()


def iter_block_items(doc: Document) -> Iterable[Any]:
    """
    Yield paragraphs and tables in document order.
    python-docx keeps them in separate collections, so we walk the XML body
    to preserve the original sequence.
    """
    for child in doc.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, doc)
        elif child.tag.endswith("}tbl"):
            yield Table(child, doc)


def serialize_table_rows(rows: List[List[str]]) -> str:
    """
    Render a table into readable text for prompts / logs / chunking.
    """
    if not rows:
        return ""

    lines = []
    for row in rows:
        lines.append(" | ".join(cell.strip() for cell in row))
    return "\n".join(lines)


def extract_table(table: Table) -> Dict[str, Any]:
    """
    Convert a DOCX table into a structured block.
    """
    rows: List[List[str]] = []
    for row in table.rows:
        rows.append([cell.text.strip() for cell in row.cells])

    return {
        "type": "table",
        "text": serialize_table_rows(rows),
        "rows": rows,
        "source": "table",
    }


def extract_blocks(docx_path: str) -> List[Dict[str, Any]]:
    logger.info("extract_blocks: opening document path=%s", docx_path)
    doc = Document(docx_path)

    blocks: List[Dict[str, Any]] = []
    skipped_empty = 0
    soft_headings = 0
    table_count = 0

    for item in iter_block_items(doc):
        # Paragraphs
        if isinstance(item, Paragraph):
            text = (item.text or "").strip()
            style = item.style.name if item.style else ""

            if not text:
                skipped_empty += 1
                continue

            if style.startswith("Heading"):
                try:
                    level = int(style.split(" ")[1])
                except (IndexError, ValueError):
                    level = 1

                blocks.append({
                    "type": "heading",
                    "text": text,
                    "level": level,
                    "source": "style",
                })
                continue

            if "List" in style or "Bullet" in style:
                blocks.append({
                    "type": "bullet",
                    "text": text,
                    "source": "style",
                })
                continue

            if looks_like_soft_heading(text):
                soft_headings += 1
                blocks.append({
                    "type": "heading",
                    "text": text,
                    "level": 1,
                    "source": "heuristic",
                })
                continue

            blocks.append({
                "type": "paragraph",
                "text": text,
                "source": "paragraph",
            })
            continue

        # Tables
        if isinstance(item, Table):
            table_count += 1
            table_block = extract_table(item)
            blocks.append(table_block)
            continue

    logger.info(
        "extract_blocks: created %d blocks, skipped %d empty paragraphs, soft headings=%d, tables=%d",
        len(blocks),
        skipped_empty,
        soft_headings,
        table_count,
    )

    return blocks