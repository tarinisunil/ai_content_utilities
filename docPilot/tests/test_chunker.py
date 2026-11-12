from pprint import pprint
from docpilot.ingestion.chunker import (
    split_large_text,
    split_long_word,
    chunk_documents,
    detect_heading,
    split_markdown_sections,
    split_preserving_format,
    split_by_paragraphs,
    split_code_block,
    identify_markdown_blocks,
    split_markdown_content,
    chunk_documents,
    generate_chunk_id,
    update_heading_stack,
    create_code_fragments,
    split_markdown_content_with_metadata,
    detect_code_fence,
    is_opening_fence,
    is_closing_fence,
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

def test_split_by_paragraphs():
    text = (
        "Python is easy to learn.\n\n"
        "Python is used in AI.\n\n"
        "Python supports automation."
    )

    chunks = split_by_paragraphs(text, max_size=50)

    assert len(chunks) == 2

    assert chunks[0] == (
        "Python is easy to learn.\n\n"
        "Python is used in AI.\n\n"
    )

    assert chunks[1] == "Python supports automation."

    # Verify that the original text is preserved
    assert "".join(chunks) == text

    # Verify that all chunks respect the size limit
    assert all(len(chunk) <= 50 for chunk in chunks)

def test_paragraph_formatting_preserved():
    text = "def greet():\n    print('Hello')"

    chunks = split_by_paragraphs(text, max_size=100)

    assert chunks == [text]


def test_empty_text_returns_no_chunks():
    assert split_by_paragraphs("", max_size=100) == []

def test_oversized_paragraph():
    text = "A" * 250

    chunks = split_by_paragraphs(text, max_size=100)

    assert len(chunks) == 3
    assert [len(chunk) for chunk in chunks] == [100, 100, 50]
    assert "".join(chunks) == text


def test_short_paragraphs():
    text = "Hello World\n\nPython is great"

    chunks = split_by_paragraphs(text, max_size=20)

    assert chunks == [
        "Hello World\n\n",
        "Python is great"
    ]

    assert "".join(chunks) == text
    assert all(len(chunk) <= 20 for chunk in chunks)



def test_all_chunks_respect_size_limit():
    text = "A" * 250 + "\n\n" + "Short paragraph"

    chunks = split_by_paragraphs(text, max_size=100)

    assert all(len(chunk) <= 100 for chunk in chunks)


def test_code_block_preserves_formatting():
    text = (
        "def greet():\n"
        "    message = 'Hello'\n"
        "    print(message)\n"
    )

    chunks = split_code_block(text, max_size=30)

    assert "".join(chunks) == text
    assert all(len(chunk) <= 30 for chunk in chunks)


def test_code_block_kept_together_when_small():
    text = "def greet():\n    print('Hello')\n"

    chunks = split_code_block(text, max_size=100)

    assert chunks == [text]


def test_oversized_code_line():
    text = "A" * 250

    chunks = split_code_block(text, max_size=100)

    assert [len(chunk) for chunk in chunks] == [100, 100, 50]
    assert "".join(chunks) == text


def test_empty_code_block():
    assert split_code_block("", max_size=100) == []

def test_identify_markdown_blocks():
    fence = "`" * 3

    text = (
        "Python is useful.\n\n"
        f"{fence}python\n"
        "def greet():\n"
        '    print("Hello")\n'
        f"{fence}\n\n"
        "This function prints a greeting."
    )

    blocks = identify_markdown_blocks(text)
    for index, block in enumerate(blocks, start=1):
        print(f"\nBlock {index}")
        print(f"Type: {block['type']}")
        print(f"Content:\n{block['content']}")
        print("-" * 40)
    assert len(blocks) == 3

    assert blocks[0]["type"] == "text"
    assert blocks[1]["type"] == "code"
    assert blocks[2]["type"] == "text"

    assert '    print("Hello")' in blocks[1]["content"]

    # Verify that no characters were lost
    assert "".join(block["content"] for block in blocks) == text

def test_split_markdown_content():
    fence = "`" * 3

    text = (
        "Python is useful.\n\n"
        f"{fence}python\n"
        "def greet():\n"
        '    print("Hello")\n'
        f"{fence}\n\n"
        "This function prints a greeting."
    )

    chunks = split_markdown_content(text, max_size=70)

    # Verify all original characters are preserved
    assert "".join(chunks) == text

    # Verify size limits
    assert all(len(chunk) <= 70 for chunk in chunks)

    # Verify code indentation is preserved
    assert '    print("Hello")' in "".join(chunks)

    # Verify at least two chunks were generated
    assert len(chunks) >= 2

def test_chunk_documents_preserves_code_formatting():
    fence = "`" * 3

    content = (
        "# Python Guide\n\n"
        "## Python Example\n\n"
        f"{fence}python\n"
        "def greet():\n"
        "    # Print a greeting\n"
        '    print("Hello")\n'
        f"{fence}\n"
    )

    documents = [{
        "title": "Python Guide",
        "source": "python.md",
        "extension": ".md",
        "content": content
    }]

    chunks = chunk_documents(documents, max_size=1000)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk["title"] == "Python Guide"
    assert chunk["heading"] == "Python Example"
    assert chunk["source"] == "python.md"

    assert "def greet():\n" in chunk["content"]
    assert '    print("Hello")' in chunk["content"]
    assert "# Print a greeting" in chunk["content"]
    assert f"{fence}python" in chunk["content"]

def test_chunk_id_is_deterministic():
    id1 = generate_chunk_id(
        "docker.md",
        0,
        "Install Docker."
    )

    id2 = generate_chunk_id(
        "docker.md",
        0,
        "Install Docker."
    )

    assert id1 == id2


def test_chunk_id_changes_with_content():
    id1 = generate_chunk_id(
        "docker.md",
        0,
        "Install Docker."
    )

    id2 = generate_chunk_id(
        "docker.md",
        0,
        "Configure Docker."
    )

    assert id1 != id2


def test_chunk_id_changes_with_source():
    id1 = generate_chunk_id(
        "docker.md",
        0,
        "Install Docker."
    )

    id2 = generate_chunk_id(
        "python.md",
        0,
        "Install Docker."
    )

    assert id1 != id2

def test_update_heading_stack():
    stack = []

    update_heading_stack(stack, 1, "Docker Guide")
    assert stack == [(1, "Docker Guide")]

    update_heading_stack(stack, 2, "Installation")
    assert stack == [
        (1, "Docker Guide"),
        (2, "Installation")
    ]

    update_heading_stack(stack, 3, "Linux")
    assert stack == [
        (1, "Docker Guide"),
        (2, "Installation"),
        (3, "Linux")
    ]

    update_heading_stack(stack, 2, "Troubleshooting")
    assert stack == [
        (1, "Docker Guide"),
        (2, "Troubleshooting")
    ]

def test_heading_hierarchy():
    content = """# Docker Guide

## Installation

### Linux
Install Docker using apt.

### Windows
Install Docker Desktop.

## Troubleshooting

### Linux
Check Docker service logs.
"""

    sections = split_markdown_sections(content)

    assert len(sections) == 3

    assert sections[0]["heading_path"] == [
        "Docker Guide",
        "Installation",
        "Linux"
    ]

    assert sections[1]["heading_path"] == [
        "Docker Guide",
        "Installation",
        "Windows"
    ]

    assert sections[2]["heading_path"] == [
        "Docker Guide",
        "Troubleshooting",
        "Linux"
    ]

def test_create_code_fragments():
    text = "A" * 250

    fragments = create_code_fragments(
        text=text,
        source="python.md",
        block_index=0,
        max_size=100
    )

    assert len(fragments) == 3

    # All fragments belong to the same block
    block_ids = {
        fragment["block_id"]
        for fragment in fragments
    }

    assert len(block_ids) == 1

    # Verify fragment positions
    assert [
        fragment["fragment_index"]
        for fragment in fragments
    ] == [0, 1, 2]

    # Verify total fragment count
    assert all(
        fragment["fragment_count"] == 3
        for fragment in fragments
    )

    # Verify size limits
    assert all(
        len(fragment["content"]) <= 100
        for fragment in fragments
    )

    # Verify no content was lost
    assert "".join(
        fragment["content"]
        for fragment in fragments
    ) == text

def test_markdown_content_with_metadata():
    fence = "`" * 3

    text = (
        "Introduction.\n\n"
        f"{fence}python\n"
        + "    print('Hello')\n" * 20
        + f"{fence}\n\n"
        + "Explanation."
    )

    chunks = split_markdown_content_with_metadata(
        text=text,
        source="python.md",
        max_size=100
    )

    # Every chunk respects the size limit
    assert all(len(c["content"]) <= 100 for c in chunks)

    # No characters are lost
    assert "".join(c["content"] for c in chunks) == text

    code_chunks = [
        c for c in chunks
        if c["block_type"] == "code"
    ]

    # Large code block produces multiple fragments
    assert len(code_chunks) > 1

    # All fragments share the same block ID
    assert len({
        c["block_id"] for c in code_chunks
    }) == 1

    # Fragment indices are sequential
    assert [
        c["fragment_index"] for c in code_chunks
    ] == list(range(len(code_chunks)))

    # Each fragment records the total count
    assert all(
        c["fragment_count"] == len(code_chunks)
        for c in code_chunks
    )

def test_code_blocks_in_different_sections_have_different_ids():
    fence = "`" * 3

    code = (
        f"{fence}python\n"
        "print('Hello')\n"
        f"{fence}\n"
    )

    content = (
        "# Docker Guide\n\n"
        "## Installation\n"
        + code
        + "\n## Troubleshooting\n"
        + code
    )

    documents = [{
        "title": "Docker Guide",
        "source": "docker.md",
        "extension": ".md",
        "content": content
    }]

    chunks = chunk_documents(documents, max_size=1000)

    code_chunks = [
        chunk for chunk in chunks
        if chunk["block_type"] == "code"
    ]

    assert len(code_chunks) == 2

    assert code_chunks[0]["block_id"] != code_chunks[1]["block_id"]

    assert code_chunks[0]["heading"] == "Installation"
    assert code_chunks[1]["heading"] == "Troubleshooting"

def test_pipeline_respects_chunk_size():
    documents = [{
        "title": "Python Guide",
        "source": "python.md",
        "extension": ".md",
        "content": "# Python Guide\n\n" + "Python is useful. " * 100
    }]

    chunks = chunk_documents(documents, max_size=100)

    assert len(chunks) > 1
    assert all(len(chunk["content"]) <= 100 for chunk in chunks)

def test_pipeline_chunk_ids_are_deterministic():
    documents = [{
        "title": "Docker Guide",
        "source": "docker.md",
        "extension": ".md",
        "content": "# Docker Guide\n\n## Installation\nInstall Docker."
    }]

    first_run = chunk_documents(documents, max_size=100)
    second_run = chunk_documents(documents, max_size=100)

    assert [c["chunk_id"] for c in first_run] == [
        c["chunk_id"] for c in second_run
    ]


def test_pipeline_preserves_heading_hierarchy():
    content = (
        "# Docker Guide\n\n"
        "## Installation\n\n"
        "### Linux\n"
        "Install Docker.\n\n"
        "## Troubleshooting\n\n"
        "### Linux\n"
        "Check Docker logs.\n"
    )

    documents = [{
        "title": "Docker Guide",
        "source": "docker.md",
        "extension": ".md",
        "content": content
    }]

    chunks = chunk_documents(documents, max_size=1000)

    assert [c["heading_path"] for c in chunks] == [
        ["Docker Guide", "Installation", "Linux"],
        ["Docker Guide", "Troubleshooting", "Linux"]
    ]

def test_pipeline_preserves_code_indentation():
    fence = "`" * 3

    content = (
        "# Python Guide\n\n"
        "## Example\n\n"
        f"{fence}python\n"
        "def greet():\n"
        '    print("Hello")\n'
        f"{fence}\n"
    )

    documents = [{
        "title": "Python Guide",
        "source": "python.md",
        "extension": ".md",
        "content": content
    }]

    chunks = chunk_documents(documents, max_size=1000)

    code_chunks = [
        c for c in chunks
        if c["block_type"] == "code"
    ]

    assert len(code_chunks) == 1
    assert '    print("Hello")' in code_chunks[0]["content"]
    assert code_chunks[0]["heading"] == "Example"


def test_structured_splitter_preserves_content():
    fence = "`" * 3

    text = (
        "Introduction.\n\n"
        f"{fence}python\n"
        "def greet():\n"
        '    print("Hello")\n'
        f"{fence}\n\n"
        "Explanation."
    )

    chunks = split_markdown_content_with_metadata(
        text=text,
        source="python.md",
        max_size=50
    )

    reconstructed = "".join(
        chunk["content"]
        for chunk in chunks
    )

    assert reconstructed == text


def test_pipeline_empty_documents():
    assert chunk_documents([], max_size=100) == []

    documents = [{
        "title": "Empty",
        "source": "empty.md",
        "extension": ".md",
        "content": ""
    }]

    assert chunk_documents(documents, max_size=100) == []


def test_shorter_tilde_fence_does_not_close_block():
    opening = "~" * 4
    shorter = "~" * 3

    text = (
        f"{opening}python\n"
        'print("Hello")\n'
        f"{shorter}\n"
        'print("Still inside")\n'
        f"{opening}\n"
    )

    blocks = identify_markdown_blocks(text)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "code"
    assert blocks[0]["content"] == text

def test_detect_code_fence():
    fence = detect_code_fence("````python")

    assert fence == {
        "character": "`",
        "length": 4,
        "remaining": "python"
    }


def test_tilde_fence_detection():
    fence = detect_code_fence("~~~python")

    assert fence["character"] == "~"
    assert fence["length"] == 3


def test_short_fence_is_not_valid():
    assert detect_code_fence("``") is None


def test_closing_fence_must_match():
    opening = detect_code_fence("````python")

    short_closing = detect_code_fence("```")
    valid_closing = detect_code_fence("````")

    assert not is_closing_fence(
        short_closing,
        opening["character"],
        opening["length"]
    )

    assert is_closing_fence(
        valid_closing,
        opening["character"],
        opening["length"]
    )


def test_section_splitter_handles_long_fences():
    opening = "`" * 4
    shorter = "`" * 3

    content = (
        "## Python Example\n\n"
        f"{opening}python\n"
        f"{shorter}\n"
        "# This is a code comment\n"
        f"{opening}\n\n"
        "## Installation\n"
        "Install the package.\n"
    )

    sections = split_markdown_sections(content)

    assert len(sections) == 2
    assert sections[0]["heading"] == "Python Example"
    assert sections[1]["heading"] == "Installation"

    assert "# This is a code comment" in sections[0]["content"]
