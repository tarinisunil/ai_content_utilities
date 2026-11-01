# Building DocPilot Part 2: From Raw Documentation to a Markdown Ingestion Pipeline

*Building the foundation of a local-first documentation search and AI knowledge assistant using Python.*

In [Part 1: Why I'm Building DocPilot](https://ai-content-utilties.hashnode.dev/why-i-m-building-docpilot-from-documentation-search-to-ai-powered-knowledge-systems), I introduced DocPilot, a local-first, self-hosted documentation search and knowledge assistant I'm building to explore information retrieval, embeddings, Retrieval-Augmented Generation (RAG), and AI agents.

Before implementing semantic search, vector databases, or integrating an LLM, there is a more fundamental problem:

**How do we take a directory containing documentation files and transform them into structured data that a search system can process?**

That's where document ingestion comes in.

In Part 2, I built DocPilot's first working component: a **Markdown document ingestion pipeline using Python**. It discovers Markdown files recursively, reads UTF-8 content, extracts titles from the first H1 heading (falling back to filenames), preserves source metadata, skips empty files, ignores JSON and TXT files, and is validated with pytest.

There are no embeddings, vector databases, or LLMs yet—and that's intentional.

---

## 1. Why Document Ingestion Comes First

AI-powered documentation search often brings to mind embeddings, vector databases, and RAG. But all of these depend on having reliable document content in the first place.

A repository may contain README files, Markdown guides, API references, JSON configuration, plain-text notes, and nested documentation folders. DocPilot needs a predictable way to discover and read the files it supports.

**Document ingestion** is the process of collecting content and converting it into a representation suitable for downstream processing.

```text
Documentation Directory
         |
         v
   File Discovery
         |
         v
 File Type Filtering
         |
         v
  Content Extraction
         |
         v
 Metadata Extraction
         |
         v
 Structured Documents
```

File discovery finds candidate files; filtering selects supported formats; content extraction reads text; and metadata extraction records the title and source path. These records will later feed chunking, indexing, and retrieval.

## 2. Setting Up the DocPilot Project

I organized the project into source code, sample documentation, and tests:

```text
docpilot/
├── examples/
│   └── sample-docs/
│       ├── getting-started.md
│       ├── architecture.md
│       ├── api-reference.md
│       ├── config.json
│       └── notes.txt
├── src/
│   └── docpilot/
│       ├── __init__.py
│       └── ingestion/
│           ├── __init__.py
│           ├── loader.py
│           └── models.py
├── tests/
│   └── test_loader.py
├── requirements.txt
├── pytest.ini
└── README.md
```

*Illustrative structure showing the main project components.*

The `src/` layout separates application code from tests and example files. Future modules for chunking, indexing, and retrieval can be added without turning the loader into one large script.

I created a virtual environment:

```bash
python -m venv venv
```

On Linux/macOS:

```bash
source venv/bin/activate
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

My `requirements.txt` initially needs only pytest:

```text
pytest>=8.0,<10.0
```

Install dependencies with:

```bash
python -m pip install -r requirements.txt
```

The loader itself uses only Python's standard library.

## 3. Creating a Sample Documentation Collection

I placed sample Markdown, JSON, and TXT files inside `examples/sample-docs/`. Including unsupported formats was deliberate: I wanted to verify that the Markdown loader **ignores files it does not claim to support**.

Markdown is a natural first format for DocPilot because technical repositories commonly use it for README files, developer guides, architecture notes, and runbooks. It also contains structure that we can use later:

```markdown
# Getting Started with DocPilot

## Installation

Install the required dependencies.

## Configuration

Update the application configuration.
```

Rather than immediately building parsers for every format, I started with one clearly defined responsibility.

## 4. Building the Markdown Loader

The implementation lives in `src/docpilot/ingestion/loader.py`.

### Step 1: Discover Markdown files recursively

```python
from pathlib import Path

root = Path(directory).resolve()

for file_path in sorted(root.rglob("*.md")):
    if not file_path.is_file():
        continue
```

`rglob("*.md")` searches nested folders and selects Markdown files, leaving JSON and TXT files out. `sorted()` makes discovery order predictable, which is helpful for debugging and tests.

### Step 2: Read content and skip empty files

```python
content = file_path.read_text(encoding="utf-8")

if not content.strip():
    continue
```

Reading as UTF-8 handles ordinary Markdown text. Skipping whitespace-only files prevents empty records from flowing into later stages.

### Step 3: Extract titles from Markdown headings

Initially, a simple option was to use the filename as the title. But `getting-started.md` might actually begin with:

```markdown
# Getting Started with DocPilot
```

The heading is more descriptive than `getting-started`, so I introduced a helper:

```python
def extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()

    return fallback
```

The function scans lines until it finds the first H1 heading beginning with `# `. It strips the heading marker and returns the text. If there is no matching heading, it uses the filename without the extension.

This is intentionally lightweight parsing, not a complete Markdown parser. For example, it does not yet handle YAML frontmatter titles or every valid Markdown heading syntax.

### Step 4: Preserve metadata

Each file becomes a record with four fields:

```python
document = {
    "title": extract_title(content, file_path.stem),
    "source": file_path.relative_to(root).as_posix(),
    "content": content,
    "extension": file_path.suffix,
}
```

| Field | Purpose |
| --- | --- |
| `title` | First H1 heading, or filename fallback |
| `source` | Relative path to the original file |
| `content` | Complete Markdown content |
| `extension` | Original file extension |

Preserving the source path matters because future search results and AI answers should be traceable back to the original documentation.

### Complete loader

```python
from pathlib import Path


def extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()

    return fallback


def load_markdown_files(directory: str):
    documents = []
    root = Path(directory).resolve()

    for file_path in sorted(root.rglob("*.md")):
        if not file_path.is_file():
            continue

        content = file_path.read_text(encoding="utf-8")
        if not content.strip():
            continue

        document = {
            "title": extract_title(content, file_path.stem),
            "source": file_path.relative_to(root).as_posix(),
            "content": content,
            "extension": file_path.suffix,
        }
        documents.append(document)

    return documents
```

Raw Markdown files go in; structured document records come out.

## 5. Inspecting the Ingestion Results

I added diagnostic output to see which files were loaded and which titles were extracted:

```python
documents = load_markdown_files("examples/sample-docs")

for index, document in enumerate(documents, start=1):
    print(f"\nDocument {index}")
    print(f"Title: {document['title']}")
    print(f"Source: {document['source']}")
    print(f"Characters: {len(document['content'])}")
    print(f"Extension: {document['extension']}")
```

For example, a file `getting-started.md` beginning with `# Getting Started with DocPilot` produces the title `Getting Started with DocPilot`, while its source remains `getting-started.md`.

**[Insert screenshot: Actual loaded paths and extracted titles]**

This is a useful early check: the loader should preserve both a human-readable title and a reference to the original file.

## 6. Testing the Ingestion Pipeline with pytest

I keep automated tests in `tests/test_loader.py`. The project-root `pytest.ini` contains:

```ini
[pytest]
pythonpath = src
testpaths = tests
addopts = -v
```

### Test actual sample documents

```python
from pathlib import Path
from docpilot.ingestion.loader import load_markdown_files, extract_title

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DOCS = PROJECT_ROOT / "examples" / "sample-docs"


def test_load_sample_documents():
    assert SAMPLE_DOCS.is_dir()
    documents = load_markdown_files(str(SAMPLE_DOCS))
    assert len(documents) > 0
    for document in documents:
        assert document["title"]
        assert document["source"].endswith(".md")
        assert document["content"].strip()
```

### Test empty files

```python
def test_empty_markdown_file(tmp_path):
    file = tmp_path / "empty.md"
    file.write_text("", encoding="utf-8")
    assert load_markdown_files(str(tmp_path)) == []
```

### Test nested directories

```python
def test_nested_markdown_files(tmp_path):
    folder = tmp_path / "guides"
    folder.mkdir()
    (folder / "installation.md").write_text(
        "# Installation", encoding="utf-8"
    )
    documents = load_markdown_files(str(tmp_path))
    assert len(documents) == 1
    assert documents[0]["source"] == "guides/installation.md"
```

### Test unsupported formats

```python
def test_ignore_non_markdown_files(tmp_path):
    (tmp_path / "config.json").write_text(
        '{"debug": true}', encoding="utf-8"
    )
    (tmp_path / "notes.txt").write_text(
        "Some notes", encoding="utf-8"
    )
    assert load_markdown_files(str(tmp_path)) == []
```

### Test heading-based titles and fallback

These are additional focused tests for the new title extraction behavior:

```python
def test_extract_title_from_heading():
    content = "# Getting Started with DocPilot\n\nSome content."
    assert extract_title(content, "getting-started") == (
        "Getting Started with DocPilot"
    )


def test_extract_title_fallback():
    content = "This document has no H1 heading."
    assert extract_title(content, "untitled-document") == (
        "untitled-document"
    )
```

Run tests with:

```bash
python -m pytest -s -v
```

My ingestion tests passed. The title-extraction tests shown above provide additional coverage to run after adding the helper.

**[Insert screenshot: Passing pytest results, including title extraction tests after running them]**

Automated tests are especially valuable now: as I add chunking or new loaders, they can catch regressions in file discovery and metadata extraction.

## 7. Design Decisions and Trade-offs

### Keep ingestion separate from search

The loader discovers, reads, and describes documents. It does not generate embeddings or write to a vector database. This keeps the component independent of future retrieval choices.

### Support Markdown first

JSON and TXT samples are present, but not ingested. Additional formats can later use dedicated loaders with their own parsing rules.

### Prefer content-aware titles, with a fallback

A Markdown H1 heading is often more meaningful than a filename. Falling back to the filename keeps documents without an H1 usable.

### Preserve source information

Relative paths will help DocPilot show evidence and link search results back to their original files.

### Start simple

For now, dictionaries and standard-library functions are enough. Typed models, stronger validation, and persistence can be introduced when needed.

## 8. Current Limitations

The pipeline works for its tested scenarios, but it is not a complete ingestion system yet:

- **Basic title parsing:** `extract_title()` recognizes lines starting exactly with `# `; it does not parse frontmatter or all Markdown heading styles.
- **Markdown-only support:** JSON and TXT are deliberately ignored.
- **Basic error handling:** malformed encodings and inaccessible files need more deliberate handling.
- **No incremental ingestion:** files are read again on every run.
- **No chunking:** each file is still a single document record.
- **No persistent index:** extracted records remain in memory.

These are useful boundaries for future iterations, not reasons to add every feature immediately.

## 9. What I Learned

**Start with data before AI.** A retrieval system needs dependable input before embeddings or LLMs can add value.

**Metadata is part of retrieval quality.** Titles and source paths make documents easier to identify and future answers easier to verify.

**Small functions are easier to test.** Separating `extract_title()` from `load_markdown_files()` makes each responsibility clearer.

**Tests define behavior.** Empty-file handling, nested discovery, format filtering, and title fallback are now explicit expectations.

**Build incrementally.** A working ingestion layer is a better foundation than an oversized first version with many loosely tested components.

## 10. What's Next: Document Chunking

DocPilot can now read Markdown files and return structured document records. But what if one file contains thousands of words across installation, configuration, authentication, and troubleshooting sections?

Treating the entire document as one retrieval unit can make it difficult to isolate the most relevant passage.

In **Part 3**, I'll explore document chunking: splitting documents into smaller, meaningful units while preserving headings, code blocks, source paths, and section context. I'll compare fixed-size approaches with Markdown-aware strategies before moving toward indexing and search.

## Conclusion

In Part 1, DocPilot was an idea and an initial architecture. In Part 2, it became a working component.

I built a Python-based Markdown ingestion pipeline that discovers files recursively, reads their contents, extracts H1-based titles with filename fallback, preserves source metadata, skips empty files, and ignores unsupported formats. I also added automated tests to validate the loader.

The implementation is intentionally small, but it establishes a foundation for the next stage: transforming complete documents into meaningful retrieval units.

**Next in the series: Building DocPilot Part 3 — Document Chunking Strategies for Better Retrieval.**

---

*DocPilot is an ongoing learning and engineering project focused on building a local-first, inspectable documentation search and AI knowledge assistant. I'm documenting the implementation, architectural decisions, experiments, and lessons as the project evolves.*
