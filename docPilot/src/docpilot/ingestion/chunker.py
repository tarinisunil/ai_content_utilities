def split_long_word(word: str, max_size: int) -> list[str]:
    if max_size <= 0:
        raise ValueError("max_size must be positive")

    pieces = []

    for i in range(0, len(word), max_size):
        pieces.append(word[i:i + max_size])

    return pieces


def split_large_text(text: str, max_size: int = 1000, debug: bool = False) -> list[str]:
    if max_size <= 0:
        raise ValueError("max_size must be positive")

    chunks = []
    current_chunk = ""

    for word in text.split():
        if debug:
            print(f"\nProcessing word: {word!r}")
            print(f"Current chunk: {current_chunk!r}")
            print(f"Completed chunks: {chunks}")
        if len(word) > max_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            chunks.extend(split_long_word(word, max_size))
            continue

        separator = 1 if current_chunk else 0

        if len(current_chunk) + len(word) + separator > max_size:
            chunks.append(current_chunk)
            current_chunk = word
        else:
            if current_chunk:
                current_chunk += " " + word
            else:
                current_chunk = word

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def chunk_documents(
        documents: list[dict],
        max_size: int = 1000,
        debug: bool = False
) -> list[dict]:

    if max_size <= 0:
        raise ValueError("max_size must be positive")

    all_chunks = []

    for document in documents:

        # Step 1: Split document into Markdown sections
        sections = split_markdown_sections(document["content"])

        # Start chunk numbering for each document
        chunk_index = 0

        if debug:
            print(f"\nDocument: {document['title']}")
            print(f"Sections found: {len(sections)}")

        # Step 2: Process each Markdown section
        for section in sections:

            if debug:
                print(f"\nHeading: {section['heading']}")

            # Step 3: Split large sections into smaller chunks
            text_chunks = split_preserving_format(
                section["content"],
                max_size=max_size
            )

            # Step 4: Add metadata to every chunk
            for text in text_chunks:

                chunk = {
                    "title": document["title"],
                    "source": document["source"],
                    "extension": document["extension"],
                    "heading": section["heading"],
                    "chunk_index": chunk_index,
                    "content": text
                }

                all_chunks.append(chunk)

                if debug:
                    print("\n--- Chunk Created ---")
                    print(f"Index: {chunk_index}")
                    print(f"Heading: {section['heading']}")
                    print(f"Content: {text}")

                chunk_index += 1

    return all_chunks


def detect_heading(line: str):
    line = line.strip()

    if not line.startswith("#"):
        return None

    level = len(line) - len(line.lstrip("#"))

    if level > 6:
        return None

    if len(line) <= level or line[level] != " ":
        return None

    heading = line[level:].strip()

    if not heading:
        return None

    return level, heading

def split_markdown_sections(content: str) -> list[dict]:
    sections = []
    current_heading = None
    current_content = []

    inside_code_block = False
    fence_char = None
    fence_length = 0

    for line in content.splitlines():
        stripped = line.strip()

        # Check whether we're opening or closing a code block.
        if not inside_code_block:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence_char = stripped[0]
                fence_length = len(stripped) - len(
                    stripped.lstrip(fence_char)
                )
                inside_code_block = True

                current_content.append(line)
                continue

        else:
            # Check for a matching closing fence.
            if stripped.startswith(fence_char * fence_length):
                remaining = stripped.lstrip(fence_char)

                if remaining == "":
                    inside_code_block = False
                    fence_char = None
                    fence_length = 0

            current_content.append(line)
            continue

        # Only detect headings outside code blocks.
        heading_info = detect_heading(line)

        if heading_info is not None:
            section_text = "\n".join(current_content).strip()

            if section_text:
                sections.append({
                    "heading": current_heading,
                    "content": section_text
                })

            level, heading = heading_info
            current_heading = heading
            current_content = []

        else:
            current_content.append(line)

    # Save the final section.
    section_text = "\n".join(current_content).strip()

    if section_text:
        sections.append({
            "heading": current_heading,
            "content": section_text
        })

    return sections

def split_preserving_format(
        text: str,
        max_size: int = 1000
) -> list[str]:

    if max_size <= 0:
        raise ValueError("max_size must be positive")

    chunks = []

    for start in range(0, len(text), max_size):
        chunk = text[start:start + max_size]
        chunks.append(chunk)

    return chunks
