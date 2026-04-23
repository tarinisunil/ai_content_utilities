import logging
import sys

# Configure logging before importing llm (loads model and logs at import time).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from extractor import extract_text
from llm import generate_json
from utils import build_prompt, extract_json
from schema import DocumentSchema

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting docx-to-json pipeline")
    if len(sys.argv) < 2:
        logger.error("Missing required argument: path to .docx file")
        sys.exit(1)

    file_path = sys.argv[1]
    logger.info("Input file: %s", file_path)

    logger.info("Step 1/5: extracting text from DOCX")
    text = extract_text(file_path)
    para_lines = len(text.splitlines())
    logger.info(
        "Step 1 complete: extracted %d characters from %d non-empty paragraphs",
        len(text),
        para_lines,
    )

    logger.info("Step 2/5: building LLM prompt from extracted text")
    prompt = build_prompt(text)
    logger.info("Step 2 complete: prompt length %d characters", len(prompt))

    logger.info("Step 3/5: generating JSON via language model")
    output = generate_json(prompt)
    logger.info("Step 3 complete: raw model output length %d characters", len(output))

    logger.info("Step 4/5: parsing JSON from model output")
    data = extract_json(output)
    logger.info(
        "Step 4 complete: parsed JSON with top-level keys: %s",
        list(data.keys()) if isinstance(data, dict) else type(data).__name__,
    )

    logger.info("Step 5/5: validating against DocumentSchema")
    validated = DocumentSchema(**data)
    logger.info("Step 5 complete: validation succeeded")

    print(validated.model_dump_json(indent=2))
    logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()