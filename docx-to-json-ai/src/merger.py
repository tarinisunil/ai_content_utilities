import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    """
    Remove duplicates while preserving the original order.
    """
    seen = set()
    out = []

    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)

    return out


def _normalize_section(section: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure section objects have a consistent shape.
    """
    return {
        "heading": section.get("heading", ""),
        "path": section.get("path", []),
        "level": section.get("level", 1),
        "type": section.get("type", "general"),
        "content": section.get("content", []),
        "keywords": section.get("keywords", []),
        "confidence": section.get("confidence", 0.0),
        "notes": section.get("notes", []),
        "children": section.get("children", []),
    }


def merge_results(results: List[Any]) -> Dict[str, Any]:
    """
    Merge chunk-level LLM outputs into one document-level object.

    Expected input forms:
    - list of section arrays
    - list of section dicts
    - nested mixtures of the above

    Output:
    - title
    - sections
    - keywords
    - confidence
    - notes
    - summary
    - document_type
    """
    final = {
        "title": "",
        "sections": [],
        "keywords": [],
        "confidence": 0.0,
        "notes": [],
        "summary": "",
        "document_type": "unknown",
    }

    keyword_set = set()
    confidences = []

    for r in results:
        if isinstance(r, list):
            for section in r:
                if not isinstance(section, dict):
                    logger.warning("merge_results: skipping non-dict section: %s", type(section))
                    continue

                normalized = _normalize_section(section)
                final["sections"].append(normalized)

                for kw in normalized.get("keywords", []):
                    if kw not in keyword_set:
                        keyword_set.add(kw)
                        final["keywords"].append(kw)

                conf = normalized.get("confidence")
                if isinstance(conf, (int, float)):
                    confidences.append(float(conf))

                for note in normalized.get("notes", []):
                    if isinstance(note, str) and note.strip():
                        final["notes"].append(note.strip())

        elif isinstance(r, dict):
            # If the model ever returns a doc-level object instead of a list
            if r.get("title") and not final["title"]:
                final["title"] = r["title"]

            if r.get("summary") and not final["summary"]:
                final["summary"] = r["summary"]

            if r.get("document_type") and final["document_type"] == "unknown":
                final["document_type"] = r["document_type"]

            # Merge top-level sections if present
            sections = r.get("sections", [])
            if isinstance(sections, list):
                for section in sections:
                    if isinstance(section, dict):
                        normalized = _normalize_section(section)
                        final["sections"].append(normalized)

                        for kw in normalized.get("keywords", []):
                            if kw not in keyword_set:
                                keyword_set.add(kw)
                                final["keywords"].append(kw)

                        conf = normalized.get("confidence")
                        if isinstance(conf, (int, float)):
                            confidences.append(float(conf))

                        for note in normalized.get("notes", []):
                            if isinstance(note, str) and note.strip():
                                final["notes"].append(note.strip())

            # Merge doc-level keywords
            for kw in r.get("keywords", []):
                if isinstance(kw, str) and kw not in keyword_set:
                    keyword_set.add(kw)
                    final["keywords"].append(kw)

            # Merge doc-level confidence
            conf = r.get("confidence")
            if isinstance(conf, (int, float)):
                confidences.append(float(conf))

            # Merge doc-level notes
            for note in r.get("notes", []):
                if isinstance(note, str) and note.strip():
                    final["notes"].append(note.strip())

            # Merge title
            if not final["title"] and r.get("title"):
                final["title"] = r["title"]

            # Merge summary
            if not final["summary"] and r.get("summary"):
                final["summary"] = r["summary"]

            # Merge document type
            if final["document_type"] == "unknown" and r.get("document_type"):
                final["document_type"] = r["document_type"]

        else:
            logger.warning("merge_results: skipping unexpected result type: %s", type(r))

    if confidences:
        final["confidence"] = round(sum(confidences) / len(confidences), 2)

    final["keywords"] = _dedupe_preserve_order(final["keywords"])
    final["notes"] = _dedupe_preserve_order(final["notes"])

    logger.info(
        "merge_results: merged %d result groups into %d sections",
        len(results),
        len(final["sections"]),
    )

    return final