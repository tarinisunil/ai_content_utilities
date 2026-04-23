import json
import logging

logger = logging.getLogger(__name__)


def build_prompt(text):
    logger.debug("build_prompt: input text length=%d", len(text))
    return f"""
Extract structured data from the text and return ONLY valid JSON.

Schema:
{{
  "title": "",
  "sections": [
    {{
      "heading": "",
      "content": "",
      "bullets": []
    }}
  ],
  "keywords": [],
  "confidence": 0.0,
  "notes": []
}}

Rules:
- Return only JSON.
- Use double quotes for all strings.
- Do not include markdown, explanations, or extra text.
- Use empty strings/lists when data is missing.
- confidence must be a number from 0 to 1.
- notes must be a short list explaining confidence.

Scoring guide:
- 0.90 to 1.00: very clear structure
- 0.70 to 0.89: mostly clear
- 0.40 to 0.69: somewhat messy
- 0.00 to 0.39: very unclear

Text:
{text}

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

        start = output.find("{")
        end = output.rfind("}")
        if start == -1 or end == -1 or end <= start:
            logger.error("extract_json: no JSON object found in model output")
            raise ValueError("No JSON found") from e

        fragment = output[start : end + 1]
        logger.info(
            "extract_json: found JSON-like substring, length=%d, attempting parse",
            len(fragment),
        )
        parsed = json.loads(fragment)
        logger.info("extract_json: substring parsed successfully")
        return parsed