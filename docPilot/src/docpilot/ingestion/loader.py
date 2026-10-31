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

        content = file_path.read_text(
            encoding="utf-8"
        )

        if not content.strip():
            continue

        document = {
            "title": extract_title(content, file_path.stem),
            "source": str(file_path.relative_to(root)),
            "content": content,
            "extension": file_path.suffix,
        }

        documents.append(document)

    return documents
