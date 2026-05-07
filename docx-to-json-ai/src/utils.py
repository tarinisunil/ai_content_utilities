import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _section_to_prompt_dict(sec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reduce a section to the fields the LLM needs to see.
    This keeps prompts smaller and more stable.
    """
    return {
        "heading": sec.get("heading", ""),
        "path": sec.get("path", []),
        "level": sec.get("level", 1),
        "type": sec.get("type", "general"),
        "content": sec.get("content", []),
        "keywords": sec.get("keywords", []),
        "confidence": sec.get("confidence", 0.0),
        "notes": sec.get("notes", []),
    }


def build_prompt(sections_chunk: List[Dict[str, Any]]) -> str:
    """
    Build a strict annotation prompt for one chunk of already-structured sections.

    The model should:
    - preserve structure
    - classify sections
    - extract keywords
    - return confidence
    - avoid rewriting or hallucinating content
    """
    prompt_payload = [_section_to_prompt_dict(sec) for sec in sections_chunk]

    return f"""
You are annotating already-structured document sections.

Input sections:
{json.dumps(prompt_payload, indent=2, ensure_ascii=False)}

Your job:
1. Do NOT change the section hierarchy.
2. Do NOT merge, split, or reorder sections.
3. Do NOT rewrite content.
4. For each section, assign:
   - type: one of "intro", "methodology", "results", "conclusion", "other"
   - keywords: 3 to 7 short keywords
   - confidence: a number from 0 to 1
   - notes: short notes only if the section is ambiguous or incomplete

Rules:
- Preserve heading, path, level, and content exactly.
- Keep the original content unchanged.
- Tables may appear as content items with type "table", rows, and text.
- Return ONLY valid JSON.
- Return a JSON array with one object per input section.
- Do not wrap the JSON in markdown fences.
- Do not add explanatory text.

Return this format:

[
  {{
    "heading": "string",
    "path": ["string"],
    "level": 1,
    "type": "intro",
    "content": [
      {{"type": "paragraph", "text": "string"}},
      {{"type": "bullet", "text": "string"}},
      {{"type": "table", "text": "string", "rows": [["cell1", "cell2"]]}}
    ],
    "keywords": ["string"],
    "confidence": 0.0,
    "notes": ["string"]
  }}
]

JSON:
"""


def extract_json(output: str) -> Any:
    """
    Parse JSON from the model output.

    Supports:
    - raw JSON array/object
    - JSON embedded in extra text
    """
    logger.info("extract_json: attempting direct json.loads (output length=%d)", len(output))
    output = (output or "").strip()

    try:
        parsed = json.loads(output)
        logger.info("extract_json: parsed full output as JSON successfully")
        return parsed
    except json.JSONDecodeError as e:
        logger.warning(
            "extract_json: direct parse failed at position %s: %s; trying substring extraction",
            e.pos,
            e.msg,
        )

        # Prefer array extraction because the prompt returns a list
        start = output.find("[")
        end = output.rfind("]")

        if start != -1 and end != -1 and end > start:
            fragment = output[start : end + 1]
            logger.info(
                "extract_json: found JSON array substring, length=%d, attempting parse",
                len(fragment),
            )
            return json.loads(fragment)

        # Fallback to object extraction if the model returned an object
        start = output.find("{")
        end = output.rfind("}")

        if start != -1 and end != -1 and end > start:
            fragment = output[start : end + 1]
            logger.info(
                "extract_json: found JSON object substring, length=%d, attempting parse",
                len(fragment),
            )
            return json.loads(fragment)

        logger.error("extract_json: no JSON found in model output")
        raise ValueError("No JSON found") from e