from pprint import pprint
from docpilot.ingestion.chunker import (
    split_large_text,
    split_long_word,
    chunk_documents,
    detect_heading,
    split_markdown_sections,
    split_preserving_format
)


def test_split_long_word():
    result = split_long_word("Kubernetes", 4)

    assert result == ["Kube", "rnet", "es"]


def test_split_large_text():
    result = split_large_text(
        "Learn Kubernetes today",
        max_size=5,
    )

    assert result == [
        "Learn",
        "Kuber",
        "netes",
        "today",
    ]


def test_chunk_size_limit():
    text = "Python makes automation easier"

    chunks = split_large_text(text, max_size=10)

    assert all(len(chunk) <= 10 for chunk in chunks)


def test_empty_text():
    assert split_large_text("", max_size=10) == []

def test_chunk_documents_preserves_metadata():

    documents = [
        {
            "title": "Docker Guide",
            "source": "docker.md",
            "extension": ".md",
            "content": "Docker makes deployment easier."
        }
    ]

    chunks = chunk_documents(documents, max_size=100)

    assert len(chunks) == 1

    assert chunks[0]["title"] == "Docker Guide"
    assert chunks[0]["source"] == "docker.md"
    assert chunks[0]["extension"] == ".md"
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["content"] == "Docker makes deployment easier."

def test_detect_heading():
    assert detect_heading("# Docker Guide") == (1, "Docker Guide")
    assert detect_heading("## Installation") == (2, "Installation")
    assert detect_heading("### Linux Installation") == (3, "Linux Installation")


def test_normal_text_is_not_heading():
    assert detect_heading("Install Docker using apt.") is None
    assert detect_heading("#Docker") is None
    assert detect_heading("####### Too many hashes") is None

def test_split_markdown_sections():
    content = """# Docker Guide

## Installation

### Linux Installation
Install Docker using apt.

### Windows Installation
Install Docker Desktop.

## Configuration
Configure Docker settings.
"""

    sections = split_markdown_sections(content)

    assert len(sections) == 3

    assert sections[0]["heading"] == "Linux Installation"
    assert sections[0]["content"] == "Install Docker using apt."

    assert sections[1]["heading"] == "Windows Installation"
    assert sections[1]["content"] == "Install Docker Desktop."

    assert sections[2]["heading"] == "Configuration"
    assert sections[2]["content"] == "Configure Docker settings."


def test_chunk_documents_preserves_headings():
    documents = [
        {
            "title": "Docker Guide",
            "source": "docker.md",
            "extension": ".md",
            "content": """# Docker Guide

## Installation
Install Docker using apt.

## Configuration
Configure Docker settings.
"""
        }
    ]

    chunks = chunk_documents(documents, max_size=100)

    assert len(chunks) == 2
    assert chunks[0]["heading"] == "Installation"
    assert chunks[1]["heading"] == "Configuration"
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1


from docpilot.ingestion.chunker import split_markdown_sections


def test_headings_inside_code_blocks_are_ignored():
    content = """## Python Example

```python
def greet():
    # Print a greeting
    print("Hello")
```

## Installation
Install the package.
"""

    sections = split_markdown_sections(content)
    print("\nActual sections:")
    pprint(sections)
    # We should have only two sections
    assert len(sections) == 2

    # Verify section headings
    assert sections[0]["heading"] == "Python Example"
    assert sections[1]["heading"] == "Installation"

    # Verify the Python code is preserved
    assert "# Print a greeting" in sections[0]["content"]
    assert '    print("Hello")' in sections[0]["content"]

    # Verify code fences are preserved
    assert "```python" in sections[0]["content"]
    assert "```" in sections[0]["content"]

    # Verify Installation content
    assert sections[1]["content"] == "Install the package."

def test_split_preserving_format():
    text = "Hello\n    World"

    chunks = split_preserving_format(text, max_size=10)

    assert "".join(chunks) == text
    assert all(len(chunk) <= 10 for chunk in chunks)
