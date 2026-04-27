import json
import logging

logger = logging.getLogger(__name__)


def build_prompt(sections_chunk):
    return f"""
You are improving already structured document sections.

Input:
{json.dumps(sections_chunk, indent=2)}

Tasks:
1. Improve clarity of content (rewrite text, keep same meaning)
2. Extract 3-7 relevant keywords per section
3. Assign a confidence score (0 to 1)

Return ONLY valid JSON in this format:

[
  {{
    "heading": "string",
    "content": [
      {{"type": "paragraph", "text": "string"}},
      {{"type": "bullet", "text": "string"}}
    ],
    "keywords": ["string"],
    "confidence": 0.0
  }}
]

Rules:
- Do NOT change section structure
- Do NOT merge or split sections
- Preserve order
- Keep content concise
- Output ONLY JSON (no explanation, no markdown)

JSON:
"""


def extract_json(output):
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

        start = output.find("[") 
        end = output.rfind("]")

        if start == -1 or end == -1 or end <= start:
            logger.error("extract_json: no JSON array found in model output")
            raise ValueError("No JSON found") from e

        fragment = output[start : end + 1]

        logger.info(
            "extract_json: found JSON-like substring, length=%d, attempting parse",
            len(fragment),
        )

        parsed = json.loads(fragment)
        logger.info("extract_json: substring parsed successfully")
        return parsed