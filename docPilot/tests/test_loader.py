from pathlib import Path

from docpilot.ingestion.loader import load_markdown_files
from docpilot.ingestion.loader import extract_title

# Locate the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Actual Markdown documentation directory
SAMPLE_DOCS = PROJECT_ROOT / "examples" / "sample-docs"


def test_load_sample_documents():
    """Test ingestion of actual DocPilot sample documents."""

    assert SAMPLE_DOCS.is_dir(), "Sample docs directory not found"

    documents = load_markdown_files(str(SAMPLE_DOCS))

    assert len(documents) > 0

    print("\n========== DocPilot Ingestion ==========")

    for index, document in enumerate(documents, start=1):
        print(f"\nDocument {index}")
        print(f"Title      : {document['title']}")
        print(f"Source Path: {document['source']}")
        print(f"Characters : {len(document['content'])}")
        print(f"Extension  : {document['extension']}")

        assert document["title"]
        assert document["source"].endswith(".md")
        assert document["content"].strip()

    print(f"\nTotal documents loaded: {len(documents)}")
    print("========================================")

def test_empty_markdown_file(tmp_path):
    """Empty Markdown files should be ignored."""

    file = tmp_path / "empty.md"
    file.write_text("", encoding="utf-8")

    documents = load_markdown_files(str(tmp_path))

    assert len(documents) == 0


def test_nested_markdown_files(tmp_path):
    """Markdown files in nested directories should be discovered."""

    folder = tmp_path / "guides"
    folder.mkdir()

    file = folder / "installation.md"
    file.write_text("# Installation", encoding="utf-8")

    documents = load_markdown_files(str(tmp_path))

    assert len(documents) == 1
    assert documents[0]["source"] == "guides/installation.md"


def test_ignore_non_markdown_files(tmp_path):
    """Non-Markdown files should not be ingested."""

    file = tmp_path / "notes.txt"
    file.write_text("Some notes", encoding="utf-8")

    documents = load_markdown_files(str(tmp_path))

    assert len(documents) == 0

def test_title_after_backtick_fence():
    fence = "`" * 3

    content = (
        f"{fence}markdown\n"
        "# Example Heading\n"
        f"{fence}\n"
        "# Actual Document Title\n"
    )

    assert extract_title(content, "fallback") == "Actual Document Title"


def test_title_after_tilde_fence():
    fence = "~" * 3

    content = (
        f"{fence}markdown\n"
        "# Example Heading\n"
        f"{fence}\n"
        "# Real Title\n"
    )

    assert extract_title(content, "fallback") == "Real Title"


def test_longer_fence_with_shorter_inner_fence():
    opening = "`" * 4
    shorter = "`" * 3

    content = (
        f"{opening}markdown\n"
        f"{shorter}\n"
        "# Not the Document Title\n"
        f"{opening}\n"
        "# Actual Title\n"
    )

    assert extract_title(content, "fallback") == "Actual Title"


def test_title_fallback_when_no_h1():
    content = (
        "## Installation\n"
        "Install the application.\n"
    )

    assert extract_title(content, "installation-guide") == (
        "installation-guide"
    )

