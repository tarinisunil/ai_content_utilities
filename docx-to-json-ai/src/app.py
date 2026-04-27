import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from extractor import extract_blocks
from structure import build_sections
from chunker import chunk_sections
from llm import generate_json
from utils import build_prompt, extract_json
from merger import merge_results
from scorer import compute_confidence
from schema import DocumentSchema

logger = logging.getLogger(__name__)


def safe_generate(prompt, retries=3, delay=1.5):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            logger.info("LLM attempt %d/%d", attempt, retries)
            output = generate_json(prompt)
            parsed = extract_json(output)
            return parsed

        except Exception as e:
            last_error = e
            logger.warning("Attempt %d failed: %s", attempt, str(e))

            if attempt < retries:
                time.sleep(delay)

    logger.error("LLM failed after %d retries", retries)
    raise RuntimeError("LLM failed after retries") from last_error


def save_to_file(filename, content):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(content)
        f.write("\n\n" + "=" * 80 + "\n\n")


def process_chunks(chunks):
    results = []
    debug = "--debug" in sys.argv 

    for i, chunk in enumerate(chunks):
        logger.info("Processing chunk %d/%d", i + 1, len(chunks))

        prompt = build_prompt(chunk)

        parsed = safe_generate(prompt)

        if debug:
            save_to_file(
                "debug_prompt.txt",
                f"--- CHUNK {i+1} PROMPT ---\n{prompt}"
            )
            save_to_file(
                "debug_output.txt",
                f"--- CHUNK {i+1} OUTPUT ---\n{parsed}"
            )

        results.append(parsed)

    return results


def main():
    logger.info("Starting structured docx pipeline")

    if len(sys.argv) < 2:
        logger.error("Missing required argument: path to .docx file")
        sys.exit(1)

    file_path = sys.argv[1]

    # --- Step 1 ---
    blocks = extract_blocks(file_path)

    # --- Step 2 ---
    sections = build_sections(blocks)

    # --- Step 3 ---
    chunks = chunk_sections(sections)

    # --- Step 4 ---
    results = process_chunks(chunks)

    # --- Step 5 ---
    final_output = merge_results(results)

    # --- Step 6 (NEW) ---
    original_text = " ".join(b.get("text", "") for b in blocks)

    final_output["confidence"] = compute_confidence(
        final_output["sections"],
        original_text
    )

    # --- Step 7 (NEW) ---
    validated = DocumentSchema(**final_output)

    # --- Step 8 ---
    import json
    print(json.dumps(validated.model_dump(), indent=2, ensure_ascii=False))

    logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()