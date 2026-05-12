import argparse
import json
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from extractor import extract_blocks
from structure import build_sections, flatten_sections, render_section_tree
from chunker import chunk_sections
from llm import generate_json, configure_provider
from utils import build_prompt, extract_json
from merger import merge_results
from scorer import compute_confidence
from finalizer import finalize_document, apply_final_metadata
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


def process_chunks(chunks, debug: bool = False):
    results = []

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

    parser = argparse.ArgumentParser(description="Docx to JSON pipeline")
    parser.add_argument("docx", help="Path to .docx file")
    parser.add_argument(
        "--provider",
        choices=["openrouter", "ollama"],
        default=None,
        help="LLM provider (overrides LLM_PROVIDER env var)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model ID for the chosen provider",
    )
    parser.add_argument("--debug", action="store_true", help="Save prompts and outputs to debug files")
    args = parser.parse_args()

    if args.provider:
        configure_provider(args.provider, args.model)
        logger.info("Provider overridden via CLI: %s", args.provider)

    file_path = args.docx
    debug = args.debug

    # Step 1: extract blocks
    blocks = extract_blocks(file_path)

    # Step 2: build hierarchical section tree
    sections_tree = build_sections(blocks)

    if debug:
        print("\n=== SECTION TREE ===")
        print(render_section_tree(sections_tree))
        print("====================\n")

    # Step 3: flatten tree for chunking
    flat_sections = flatten_sections(sections_tree)
    chunks = chunk_sections(flat_sections)

    # Step 4: LLM processing on chunks
    results = process_chunks(chunks, debug=debug)

    # Step 5: merge chunk outputs
    final_output = merge_results(results)

    # Step 6: compute confidence
    original_text = " ".join(b.get("text", "") for b in blocks)
    final_output["confidence"] = compute_confidence(
        final_output["sections"],
        original_text
    )

    # Step 7: document-level metadata pass
    doc_meta = finalize_document(final_output)
    final_output = apply_final_metadata(final_output, doc_meta)

    # Step 8: validate
    validated = DocumentSchema(**final_output)

    # Step 9: print output
    print(json.dumps(validated.model_dump(), indent=2, ensure_ascii=False))

    logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()