import json
import logging
from typing import Any, Dict, List

from llm import generate_json

logger = logging.getLogger(__name__)


DOCUMENT_TYPES = [
    "report",
    "article",
    "memo",
    "proposal",
    "tutorial",
    "notes",
    "other",
]


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out = []

    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)

    return out


def _parse_json_object(output: str) -> Dict[str, Any]:
    """
    Parse a JSON object from raw model output.

    This is separate from chunk parsing because step 7 expects a JSON object,
    not a JSON array.
    """
    output = (output or "").strip()

    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = output.find("{")
    end = output.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")

    fragment = output[start : end + 1]
    parsed = json.loads(fragment)

    if not isinstance(parsed, dict):
        raise ValueError("Parsed JSON was not an object")

    return parsed


def build_final_prompt(document: Dict[str, Any]) -> str:
    """
    Build a document-level prompt from the fully merged structure.
    The model should only infer metadata, not alter structure.
    """
    payload = {
        "title": document.get("title", ""),
        "sections": document.get("sections", []),
        "keywords": document.get("keywords", []),
        "confidence": document.get("confidence", 0.0),
        "notes": document.get("notes", []),
    }

    return f"""
You are generating document-level metadata for an already-structured document.

Input document:
{json.dumps(payload, indent=2, ensure_ascii=False)}

Your job:
1. Infer a concise title.
2. Write a short summary of the whole document.
3. Classify the document type.
4. Extract 5 to 12 top-level keywords.
5. Add short notes only if the document is ambiguous.

Rules:
- Do NOT modify sections.
- Do NOT rewrite section content.
- Do NOT change section hierarchy.
- Return ONLY valid JSON.
- Return a single JSON object, not an array.
- Use double quotes for all strings.

Allowed document_type values:
{json.dumps(DOCUMENT_TYPES)}

Return this format:
{{
  "title": "string",
  "summary": "string",
  "document_type": "report",
  "keywords": ["string"],
  "notes": ["string"]
}}

JSON:
"""


def finalize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the final document-level LLM pass and return the metadata object.
    """
    prompt = build_final_prompt(document)
    raw = generate_json(prompt)
    parsed = _parse_json_object(raw)

    title = str(parsed.get("title", "")).strip()
    summary = str(parsed.get("summary", "")).strip()
    document_type = str(parsed.get("document_type", "other")).strip().lower()

    if document_type not in DOCUMENT_TYPES:
        document_type = "other"

    keywords = parsed.get("keywords", [])
    if not isinstance(keywords, list):
        keywords = []

    notes = parsed.get("notes", [])
    if not isinstance(notes, list):
        notes = []

    return {
        "title": title,
        "summary": summary,
        "document_type": document_type,
        "keywords": [str(k).strip() for k in keywords if str(k).strip()],
        "notes": [str(n).strip() for n in notes if str(n).strip()],
    }


def apply_final_metadata(document: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge final document-level metadata into the existing output.
    """
    updated = dict(document)

    if metadata.get("title"):
        updated["title"] = metadata["title"]

    if metadata.get("summary"):
        updated["summary"] = metadata["summary"]

    if metadata.get("document_type"):
        updated["document_type"] = metadata["document_type"]

    merged_keywords = list(updated.get("keywords", [])) + list(metadata.get("keywords", []))
    merged_notes = list(updated.get("notes", [])) + list(metadata.get("notes", []))

    updated["keywords"] = _dedupe_preserve_order(
        [str(k).strip() for k in merged_keywords if str(k).strip()]
    )
    updated["notes"] = _dedupe_preserve_order(
        [str(n).strip() for n in merged_notes if str(n).strip()]
    )

    return updated