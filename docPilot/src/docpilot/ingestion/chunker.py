"""Markdown-aware chunking for DocPilot.

Character limits apply to chunk content, not metadata. Heading lines are
represented as metadata; within each section, original content is retained
except for whitespace at the section's outer boundaries.
"""

import hashlib
import re
from docpilot.ingestion.chunker import (
    detect_code_fence,
    is_opening_fence,
    is_closing_fence,
)

def split_preserving_format(text: str, max_size: int = 1000) -> list[str]:
    if max_size <= 0:
        raise ValueError('max_size must be positive')
    return [text[i:i + max_size] for i in range(0, len(text), max_size)]


def split_long_word(word: str, max_size: int) -> list[str]:
    return split_preserving_format(word, max_size)


def split_large_text(text: str, max_size: int = 1000, debug: bool = False) -> list[str]:
    """Legacy learning helper: normalizes whitespace; not used in the pipeline."""
    if max_size <= 0:
        raise ValueError('max_size must be positive')
    chunks, current = [], ''
    for word in text.split():
        if debug:
            print(f'Processing word: {word!r}; current: {current!r}')
        if len(word) > max_size:
            if current:
                chunks.append(current)
                current = ''
            chunks.extend(split_long_word(word, max_size))
            continue
        candidate = f'{current} {word}' if current else word
        if len(candidate) > max_size:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def split_code_block(text: str, max_size: int = 1000) -> list[str]:
    """Prefer complete lines, preserving all original characters."""
    if max_size <= 0:
        raise ValueError('max_size must be positive')
    chunks, current = [], ''
    for line in text.splitlines(keepends=True):
        if len(line) > max_size:
            if current:
                chunks.append(current)
                current = ''
            chunks.extend(split_preserving_format(line, max_size))
        elif len(current) + len(line) <= max_size:
            current += line
        else:
            if current:
                chunks.append(current)
            current = line
    if current:
        chunks.append(current)
    return chunks


def split_by_paragraphs(text: str, max_size: int = 1000) -> list[str]:
    """Prefer blank-line boundaries; retain separators across chunk boundaries.

    Not code-aware on its own: call only for ordinary Markdown text blocks.
    """
    if max_size <= 0:
        raise ValueError('max_size must be positive')
    if not text:
        return []
    # Attach separators to the preceding paragraph to avoid losing characters.
    units = re.findall(r'.*?(?:\n[ \t]*\n+|\Z)', text, flags=re.DOTALL)
    units = [unit for unit in units if unit]
    chunks, current = [], ''
    for unit in units:
        if len(unit) > max_size:
            if current:
                chunks.append(current)
                current = ''
            chunks.extend(split_code_block(unit, max_size))
        elif len(current) + len(unit) <= max_size:
            current += unit
        else:
            if current:
                chunks.append(current)
            current = unit
    if current:
        chunks.append(current)
    return chunks


def detect_code_fence(line: str) -> dict | None:
    raw = line.rstrip('\r\n')
    candidate = raw.lstrip(' ')
    if len(raw) - len(candidate) > 3 or not candidate:
        return None
    char = candidate[0]
    if char not in ('`', '~'):
        return None
    length = len(candidate) - len(candidate.lstrip(char))
    if length < 3:
        return None
    return {'character': char, 'length': length, 'remaining': candidate[length:]}


def is_opening_fence(fence: dict | None) -> bool:
    return fence is not None and not (
        fence['character'] == '`' and '`' in fence['remaining']
    )


def is_closing_fence(fence: dict | None, opening_char: str, opening_length: int) -> bool:
    return fence is not None and (
        fence['character'] == opening_char
        and fence['length'] >= opening_length
        and fence['remaining'].strip() == ''
    )


def detect_heading(line: str) -> tuple[int, str] | None:
    # CommonMark ATX headings may have up to three leading spaces.
    candidate = line.rstrip('\r\n')
    candidate = candidate.lstrip(' ')
    if len(line.rstrip('\r\n')) - len(candidate) > 3:
        return None
    match = re.match(r'^(#{1,6})(?:[ \t]+(.*)|$)', candidate)
    if not match:
        return None
    heading = (match.group(2) or '').strip()
    # Strip optional closing hashes preceded by whitespace.
    heading = re.sub(r'[ \t]+#+[ \t]*$', '', heading).strip()
    return (len(match.group(1)), heading) if heading else None


def update_heading_stack(stack: list[tuple[int, str]], level: int, heading: str) -> list[tuple[int, str]]:
    while stack and stack[-1][0] >= level:
        stack.pop()
    stack.append((level, heading))
    return stack


def split_markdown_sections(content: str) -> list[dict]:
    """Return nonempty heading sections, ignoring headings within fenced code."""
    sections, current_lines, stack = [], [], []
    heading, heading_path = None, []
    fence_char, fence_length = None, 0

    def save_section():
        section_text = ''.join(current_lines).strip()
        if section_text:
            sections.append({
                'heading': heading,
                'heading_path': heading_path.copy(),
                'content': section_text,
            })

    for line in content.splitlines(keepends=True):
        fence = detect_code_fence(line)
        if fence_char is not None:
            current_lines.append(line)
            if is_closing_fence(fence, fence_char, fence_length):
                fence_char, fence_length = None, 0
            continue
        if is_opening_fence(fence):
            fence_char, fence_length = fence['character'], fence['length']
            current_lines.append(line)
            continue
        found = detect_heading(line)
        if found is None:
            current_lines.append(line)
            continue
        save_section()
        level, heading = found
        update_heading_stack(stack, level, heading)
        heading_path = [name for _, name in stack]
        current_lines = []
    save_section()
    return sections


def identify_markdown_blocks(text: str) -> list[dict]:
    """Identify fenced code and text blocks without altering their characters."""
    blocks, lines = [], []
    fence_char, fence_length = None, 0
    for line in text.splitlines(keepends=True):
        fence = detect_code_fence(line)
        if fence_char is None and is_opening_fence(fence):
            if lines:
                blocks.append({'type': 'text', 'content': ''.join(lines)})
            lines = [line]
            fence_char, fence_length = fence['character'], fence['length']
        elif fence_char is not None and is_closing_fence(fence, fence_char, fence_length):
            lines.append(line)
            blocks.append({'type': 'code', 'content': ''.join(lines)})
            lines = []
            fence_char, fence_length = None, 0
        else:
            lines.append(line)
    if lines:
        blocks.append({'type': 'code' if fence_char is not None else 'text', 'content': ''.join(lines)})
    return blocks


def split_markdown_content(text: str, max_size: int = 1000) -> list[str]:
    """Backward-compatible string-only splitter."""
    return [item['content'] for item in split_markdown_content_with_metadata(text, source='', max_size=max_size)]


def generate_chunk_id(source: str, chunk_index: int, content: str) -> str:
    raw = f'{source}:{chunk_index}:{content}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def create_code_fragments(text: str, source: str, block_index: int,
                          max_size: int = 1000, section_index: int = 0) -> list[dict]:
    if max_size <= 0:
        raise ValueError('max_size must be positive')
    pieces = split_code_block(text, max_size)
    block_id = generate_chunk_id(source, section_index, f'{block_index}:{text}')
    return [
        {'block_id': block_id, 'block_type': 'code',
         'fragment_index': index, 'fragment_count': len(pieces), 'content': piece}
        for index, piece in enumerate(pieces)
    ]


def split_markdown_content_with_metadata(text: str, source: str,
                                         block_index_start: int = 0,
                                         section_index: int = 0,
                                         max_size: int = 1000) -> list[dict]:
    if max_size <= 0:
        raise ValueError('max_size must be positive')
    chunks = []
    for block_index, block in enumerate(identify_markdown_blocks(text), start=block_index_start):
        if block['type'] == 'code':
            chunks.extend(create_code_fragments(block['content'], source, block_index,
                                                max_size=max_size, section_index=section_index))
        else:
            for piece in split_by_paragraphs(block['content'], max_size):
                chunks.append({'block_id': None, 'block_type': 'text',
                               'fragment_index': None, 'fragment_count': None,
                               'content': piece})
    return chunks


def chunk_documents(documents: list[dict], max_size: int = 1000,
                    debug: bool = False) -> list[dict]:
    if max_size <= 0:
        raise ValueError('max_size must be positive')
    all_chunks = []
    for document in documents:
        sections = split_markdown_sections(document['content'])
        chunk_index = 0
        if debug:
            print(f"Document: {document['title']} | Sections: {len(sections)}")
        for section_index, section in enumerate(sections):
            items = split_markdown_content_with_metadata(
                section['content'], document['source'],
                section_index=section_index, max_size=max_size)
            for item in items:
                chunk = {
                    'chunk_id': generate_chunk_id(document['source'], chunk_index, item['content']),
                    'title': document['title'],
                    'source': document['source'],
                    'extension': document['extension'],
                    'heading': section['heading'],
                    'heading_path': section['heading_path'].copy(),
                    'chunk_index': chunk_index,
                    **item,
                }
                all_chunks.append(chunk)
                if debug:
                    print(f"Chunk {chunk_index} | {chunk['heading_path']} | {chunk['block_type']} | {len(chunk['content'])} chars")
                chunk_index += 1
    return all_chunks
