import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _make_section(heading: str, level: int = 1, section_type: str = "general") -> Dict[str, Any]:
    """
    Create a new section node.

    We keep sections as dictionaries for compatibility with the rest of the
    pipeline, since chunking, merging, and validation currently work with dicts.
    """
    return {
        "heading": heading,
        "level": level,
        "type": section_type,
        "content": [],
        "children": [],
        "keywords": [],
        "confidence": 0.0,
        "notes": [],
    }


def build_sections(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert a flat block list into a hierarchical section tree.

    Rules:
    - Heading blocks start new sections.
    - Heading level determines nesting.
    - Paragraphs and bullets go into the most recent open section.
    - Content before the first heading is placed under an implicit Introduction.
    """
    root_sections: List[Dict[str, Any]] = []
    stack: List[Dict[str, Any]] = []

    for block in blocks:
        btype = block.get("type", "paragraph")
        text = (block.get("text") or "").strip()

        if not text:
            continue

        if btype == "heading":
            level = int(block.get("level", 1) or 1)

            section = _make_section(
                heading=text,
                level=level,
                section_type="general",
            )

            # Walk back to the nearest valid parent level.
            while stack and stack[-1]["level"] >= level:
                stack.pop()

            if stack:
                stack[-1]["children"].append(section)
            else:
                root_sections.append(section)

            stack.append(section)
            continue

        # If the document starts with content before any heading,
        # create a default top-level section.
        if not stack:
            intro = _make_section(
                heading="Introduction",
                level=1,
                section_type="general",
            )
            root_sections.append(intro)
            stack.append(intro)

        stack[-1]["content"].append({
            "type": btype,
            "text": text,
        })

    logger.info("build_sections: built %d root sections", len(root_sections))
    return root_sections


def flatten_sections(
    sections: List[Dict[str, Any]],
    parent_path: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Flatten a section tree into a list while preserving path metadata.

    This is useful for chunking and LLM processing, because the current chunker
    expects a list of section-like dicts with heading/content fields.
    """
    parent_path = parent_path or []
    flat: List[Dict[str, Any]] = []

    for sec in sections:
        heading = sec.get("heading", "")
        path = parent_path + [heading]

        flat.append({
            "heading": heading,
            "path": path,
            "level": sec.get("level", 1),
            "type": sec.get("type", "general"),
            "content": sec.get("content", []),
            "keywords": sec.get("keywords", []),
            "confidence": sec.get("confidence", 0.0),
            "notes": sec.get("notes", []),
        })

        children = sec.get("children", [])
        if children:
            flat.extend(flatten_sections(children, path))

    return flat


def render_section_tree(sections: List[Dict[str, Any]], indent: int = 0) -> str:
    """
    Pretty-print the tree for debugging or for a blog demo.
    """
    lines: List[str] = []

    for sec in sections:
        prefix = "  " * indent
        heading = sec.get("heading", "")
        level = sec.get("level", 1)

        lines.append(f"{prefix}- {heading} (H{level})")

        content = sec.get("content", [])
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type", "paragraph")

                if item_type == "table":
                    rows = item.get("rows", [])
                    lines.append(f"{prefix}    · [table] {len(rows)} rows")

                    if rows:
                        preview = rows[:2]
                        for row in preview:
                            if isinstance(row, list):
                                lines.append(f"{prefix}      - {' | '.join(str(cell) for cell in row)}")
                else:
                    text = (item.get("text", "") or "").strip()
                    if text:
                        lines.append(f"{prefix}    · [{item_type}] {text}")
            else:
                text = str(item).strip()
                if text:
                    lines.append(f"{prefix}    · {text}")

        children = sec.get("children", [])
        if children:
            child_tree = render_section_tree(children, indent + 1)
            if child_tree.strip():
                lines.append(child_tree)

    return "\n".join(line for line in lines if line.strip())
