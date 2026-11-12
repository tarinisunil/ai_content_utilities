from pathlib import Path


def extract_title(content: str, fallback: str) -> str:
    inside_code_block = False
    fence_char = None
    fence_length = 0

    for line in content.splitlines():
        fence = detect_code_fence(line)

        if not inside_code_block:
            if is_opening_fence(fence):
                inside_code_block = True
                fence_char = fence["character"]
                fence_length = fence["length"]
                continue

            if line.startswith("# "):
                return line[2:].strip()

        else:
            if is_closing_fence(
                fence,
                fence_char,
                fence_length
            ):
                inside_code_block = False
                fence_char = None
                fence_length = 0

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
