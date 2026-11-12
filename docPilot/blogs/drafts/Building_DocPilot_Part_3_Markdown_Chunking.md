# Building DocPilot — Part 3: From Markdown Documents to Searchable Chunks

*Building a local-first documentation assistant, one component at a time.*

In [Part 1](https://ai-content-utilties.hashnode.dev/why-i-m-building-docpilot-from-documentation-search-to-ai-powered-knowledge-systems), I introduced DocPilot, a local-first documentation search and knowledge assistant I'm building to explore embeddings, retrieval, RAG, and AI-powered knowledge systems.

In [Part 2](https://ai-content-utilties.hashnode.dev/building-docpilot-part-2-from-raw-documentation-to-a-markdown-ingestion-pipeline), I implemented the first Markdown ingestion pipeline using Python, `pathlib`, and `pytest`.

That pipeline could discover Markdown files, read their content, extract document titles, and preserve source information.

But there was an important limitation.

**DocPilot could load documents, but it couldn't yet prepare them for efficient retrieval.**

A technical document might contain installation instructions, configuration details, API references, troubleshooting guides, and code examples.

If I eventually want DocPilot to answer a question about API authentication, retrieving an entire document containing thousands of unrelated words wouldn't be ideal.

I needed a way to divide documents into smaller, meaningful pieces while preserving their structure and context.

That became the focus of Part 3: **document chunking**.

---

## 1. Understanding Document Chunking

Document chunking is the process of dividing large documents into smaller units of text called *chunks*.

Consider this Markdown document:

```markdown
# Docker Guide

## Installation
Install Docker using your package manager.

## Configuration
Configure Docker settings.

## Troubleshooting
Check Docker service logs.
```

Instead of treating the entire document as one piece, I wanted DocPilot to identify the individual sections.

For example:

```python
{
    "heading": "Installation",
    "content": "Install Docker using your package manager."
}
```

And:

```python
{
    "heading": "Troubleshooting",
    "content": "Check Docker service logs."
}
```

Why does this matter?

Suppose a user asks:

> How do I troubleshoot Docker?

A future retrieval system should be able to find the Troubleshooting section without necessarily retrieving the Installation and Configuration sections.

Chunking doesn't perform retrieval itself. It prepares the content that will later be embedded, indexed, and searched.

### Choosing a Chunking Strategy

There are several ways to divide text.

| Strategy | Approach | Trade-off |
|---|---|---|
| Fixed-size | Split after a fixed number of characters | Simple, but can break words or code |
| Word-based | Group words until a size limit is reached | Avoids most word breaks, but can lose formatting |
| Paragraph-based | Split at paragraph boundaries | Preserves related sentences |
| Heading-based | Split using Markdown headings | Preserves document structure |
| Semantic | Split based on changes in meaning | More complex and potentially computationally expensive |

Since DocPilot primarily works with Markdown documentation, I decided to begin with a **heading-aware approach**, followed by smaller splits when sections exceeded a configured size limit.

I also wanted to understand the implementation rather than immediately relying on an external chunking library.

---

## 2. My First Attempt: Word-Based Chunking

I started with a simple Python function that split text into words and grouped them into chunks.

The basic idea was:

1. Split the input into words.
2. Add words to the current chunk while they fit.
3. Save the current chunk when the next word would exceed the limit.
4. Start a new chunk.
5. Continue until all words have been processed.

The implementation used:

```python
for word in text.split():
    ...
```

I also handled unusually long words using string slicing:

```python
def split_long_word(word: str, max_size: int) -> list[str]:
    if max_size <= 0:
        raise ValueError("max_size must be positive")

    pieces = []

    for i in range(0, len(word), max_size):
        pieces.append(word[i:i + max_size])

    return pieces
```

This helped me understand Python's `range()`, string slicing, and chunk-size boundaries.

It also revealed an important edge case: a single word could exceed the configured maximum size.

However, the bigger problem appeared when I tested the chunker with actual technical documentation.

---

## 3. The First Major Problem: Losing Code Formatting

One of my sample Markdown documents contained a Python code block:

````markdown
```python
def greet():
    # Print a greeting
    print("Hello")
```
````

But when I inspected the chunking output, the code had been converted into a single line:

````text
```python def greet(): # Print a greeting print("Hello") ```
````

The indentation and line breaks were gone.

This happened because `text.split()` removes whitespace, including newlines and indentation.

When I joined the words again using spaces, I couldn't recover the original formatting.

For ordinary text, this might seem like a minor issue.

For technical documentation, it can change the meaning of the content.

Python indentation is syntactically significant. Configuration files, shell commands, and Markdown tables can also depend on their original formatting.

**I realized that a chunker shouldn't just divide text into smaller pieces. It also needs to preserve the information that makes the text understandable.**

### Preserving the Original Characters

To investigate this, I created a simple formatting-preserving splitter:

```python
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
```

Unlike word-based splitting, this function uses Python string slicing.

It preserves the original characters, including spaces and newlines.

For example:

```python
text = "def greet():\n    print('Hello')"

chunks = split_preserving_format(text, max_size=100)

assert "".join(chunks) == text
```

This solved the whitespace-loss problem.

But it introduced another limitation: fixed-character splitting could break words, sentences, or code blocks in the middle.

I needed a smarter strategy.

---

## 4. Making the Chunker Markdown-Aware

Markdown documents already contain useful structure through headings.

For example:

```markdown
# Docker Guide

## Installation

### Linux
Install Docker using apt.

### Windows
Install Docker Desktop.
```

Rather than ignoring this structure, I wanted DocPilot to use it.

I created a heading detector:

```python
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
```

The function identifies Markdown heading levels from `#` to `######`.

For example:

```python
detect_heading("### Linux Installation")
```

Returns:

```python
(3, "Linux Installation")
```

I then used this function inside `split_markdown_sections()` to group content under its corresponding heading.

This made the chunks more meaningful.

However, I soon encountered another Markdown-specific edge case.

---

## 5. Handling Headings Inside Code Blocks

Consider this Markdown:

````markdown
## Python Example

```python
def greet():
    # Print a greeting
    print("Hello")
```
````

The line:

```python
# Print a greeting
```

looks like a level-one Markdown heading if I only check whether a line starts with `# `.

But it is actually a Python comment inside a fenced code block.

If my chunker treated it as a heading, it would incorrectly divide the document.

To solve this, I introduced code-fence tracking.

The basic idea was to remember whether the parser was currently inside a fenced code block.

I also learned that Markdown supports both backtick and tilde fences:

````text
```python
print("Hello")
```
````

And:

```text
~~~python
print("Hello")
~~~
```

There was another subtle requirement.

A code block opened with four backticks cannot be closed by a line containing only three backticks.

The closing fence must use the same character and contain at least as many fence characters as the opening fence.

I eventually separated this logic into reusable helpers:

```python
detect_code_fence()
is_opening_fence()
is_closing_fence()
```

Both the heading-based section splitter and the Markdown block detector use these helpers.

This reduced duplicated logic and helped keep their interpretation of code fences consistent.

It also introduced me to the **DRY principle — Don't Repeat Yourself**.

---

## 6. Combining Paragraph and Code-Block Chunking

After handling headings and fenced code blocks, I needed to decide how to split content within each section.

I wanted different behavior for ordinary paragraphs and code examples.

### Paragraph-Aware Splitting

For ordinary text, I wanted to prefer paragraph boundaries.

Consider:

```markdown
Python is a programming language.

Python supports object-oriented programming.

Python is widely used in AI applications.
```

If the first two paragraphs fit within the maximum chunk size, they can remain together.

If adding the third would exceed the limit, the third paragraph should begin a new chunk.

An important detail was preserving the blank-line separators between paragraphs.

Originally, some tests expected:

```python
["Hello World", "Python is great"]
```

But the improved splitter returned:

```python
["Hello World\n\n", "Python is great"]
```

At first, the tests failed.

After investigating, I realized the new behavior was intentional.

The original paragraph separator belonged to the source text.

By preserving it, I could verify:

```python
assert "".join(chunks) == original_text
```

This became one of the important properties of the chunking implementation.

### Code-Block-Aware Splitting

For code, I preferred splitting at complete line boundaries.

Python provides:

```python
text.splitlines(keepends=True)
```

The `keepends=True` argument preserves newline characters.

For example:

```python
text = "AAAA\nBBBB\nCCCC\n"

print(text.splitlines(keepends=True))
```

Returns:

```python
["AAAA\n", "BBBB\n", "CCCC\n"]
```

I used this behavior in `split_code_block()`.

If an entire code block fits within the maximum size, it can remain together.

If it is too large, the splitter prefers complete lines.

If an individual line is larger than the limit, character-based splitting acts as a fallback.

This approach doesn't guarantee that every resulting code fragment is independently executable. But it preserves the original characters and enforces the configured size limit.

---

## 7. Preserving Heading Hierarchy

Another interesting problem appeared when I considered documents containing repeated headings.

For example:

```markdown
# Docker Guide

## Installation

### Linux
Install Docker using apt.

## Troubleshooting

### Linux
Check Docker service logs.
```

Both subsections are called `Linux`.

If I stored only:

```python
"heading": "Linux"
```

I would lose important context.

The first Linux section belongs to Installation, while the second belongs to Troubleshooting.

To solve this, I introduced a heading stack.

```python
def update_heading_stack(
    stack: list[tuple[int, str]],
    level: int,
    heading: str
) -> list[tuple[int, str]]:

    while stack and stack[-1][0] >= level:
        stack.pop()

    stack.append((level, heading))

    return stack
```

The stack stores heading levels and names.

When a new heading appears, headings at the same or deeper level are removed before adding the new heading.

This allows DocPilot to preserve paths such as:

```python
[
    "Docker Guide",
    "Installation",
    "Linux"
]
```

And:

```python
[
    "Docker Guide",
    "Troubleshooting",
    "Linux"
]
```

These paths will be useful when DocPilot eventually displays search results and source citations.

---

## 8. Adding Deterministic Chunk IDs

Once the chunks had meaningful structure, I needed a way to identify them.

Each chunk already had a `chunk_index`, but that index could repeat across different documents.

I introduced deterministic chunk IDs using Python's built-in `hashlib` module.

```python
import hashlib

def generate_chunk_id(
    source: str,
    chunk_index: int,
    content: str
) -> str:

    raw_value = f"{source}:{chunk_index}:{content}"

    chunk_hash = hashlib.sha256(
        raw_value.encode("utf-8")
    ).hexdigest()

    return chunk_hash
```

The ID depends on:

- The source document.
- The chunk's position.
- The chunk's content.

For unchanged inputs, the function generates the same ID.

This is useful for repeatable ingestion and future indexing.

However, it has a trade-off.

Because the ID includes the chunk index, inserting content earlier in a document may change the IDs of later chunks.

I plan to revisit this when implementing document updates and re-indexing.

---

## 9. Tracking Oversized Code Fragments

A large code block may need to be divided into several chunks.

For example, a code block containing 2,500 characters might produce multiple fragments when the configured maximum size is 1,000 characters.

Each fragment needs its own chunk ID, but all fragments should retain a relationship to their original code block.

I introduced additional metadata:

```python
{
    "block_id": "shared-parent-id",
    "block_type": "code",
    "fragment_index": 0,
    "fragment_count": 3,
    "content": "..."
}
```

Here:

- `block_id` identifies the original code block.
- `fragment_index` identifies the fragment's position.
- `fragment_count` records how many fragments belong to the block.

This prepares DocPilot for a future retrieval feature where neighboring fragments can be fetched to provide additional context.

For example, if semantic search retrieves the middle fragment of a large function, DocPilot could eventually locate the other fragments using their shared block ID.

That functionality isn't implemented yet, but the metadata makes it possible.

---

## 10. Bringing Everything Together

After building and testing the individual functions, I connected them through `chunk_documents()`.

The resulting pipeline is:

```text
Markdown Files
      |
      v
Markdown Loader
      |
      v
Heading-Aware Section Splitter
      |
      v
Markdown Block Detector
      |
      +---- Ordinary Text
      |          |
      |          v
      |    Paragraph/Line-Aware Splitting
      |
      +---- Fenced Code
                 |
                 v
           Line-Aware Splitting
                 |
                 v
          Fragment Metadata
                 |
                 v
       Structured Document Chunks
```

A final chunk can contain:

```python
{
    "chunk_id": "sha256-hash",
    "title": "Docker Guide",
    "source": "docker.md",
    "extension": ".md",
    "heading": "Linux",
    "heading_path": [
        "Docker Guide",
        "Installation",
        "Linux"
    ],
    "chunk_index": 0,
    "block_id": None,
    "block_type": "text",
    "fragment_index": None,
    "fragment_count": None,
    "content": "Install Docker using apt."
}
```

The document loader remains responsible for reading files.

The chunker is responsible for processing the loaded content.

This separation makes the system easier to test and extend.

---

## 11. Testing the Chunking Pipeline with Pytest

Testing became a major part of this implementation.

I started with simple tests for individual functions and gradually introduced more realistic Markdown scenarios.

Some of the important test cases included:

| Test scenario | What it verifies |
|---|---|
| Short text | Content remains in one chunk when appropriate |
| Oversized paragraphs | Chunks respect the configured limit |
| Python code blocks | Indentation and line breaks are preserved |
| Headings inside code | Code comments aren't mistaken for headings |
| Backtick and tilde fences | Both supported fence types are recognized |
| Longer opening fences | Shorter fences don't close the block |
| Repeated headings | Heading hierarchy is preserved |
| Deterministic IDs | Identical inputs produce identical IDs |
| Oversized code fragments | Fragment order and shared block IDs are correct |
| Empty documents | Empty input produces no chunks |

One of the most useful assertions was:

```python
assert "".join(chunks) == original_text
```

This checks that a splitter preserves the original content.

Another was:

```python
assert all(
    len(chunk) <= max_size
    for chunk in chunks
)
```

This verifies the chunk-size constraint.

For structured chunks, the same idea applies to each chunk's `content` field.

During the final cleanup, I also encountered two failing paragraph tests.

The failures occurred because the improved splitter preserved paragraph separators that the earlier tests expected to be removed.

After confirming the intended behavior, I updated the assertions to verify content preservation.

The latest complete test run passed, with 44 tests covering the ingestion and chunking functionality.

The tests don't prove that every possible Markdown edge case is handled, but they give me confidence in the scenarios I've implemented.

---

## 12. A Useful Lesson from Community Feedback

While working on this series, I received feedback on the title-extraction logic from Part 2.

My original implementation searched for the first line beginning with `# `.

That was simple, but it could incorrectly extract a title from inside a fenced code example.

For instance:

````markdown
```markdown
# Example Heading
```

# Actual Document Title
````

The original function could return `Example Heading` instead of `Actual Document Title`.

The feedback suggested testing backtick fences, tilde fences, longer opening fences, and documents without an H1 heading.

Interestingly, these were closely related to the Markdown parsing problems I was already solving in Part 3.

I reused the code-fence detection logic to improve title extraction and added tests for those scenarios.

This reinforced an important lesson:

**Building software isn't only about implementing the initial design. It's also about responding to edge cases, testing assumptions, and improving the system as new problems become visible.**

---

## 13. Challenges and Lessons Learned

This part of DocPilot took more effort than I initially expected.

At first, chunking seemed like a simple text-splitting problem.

But working with technical documentation introduced several challenges.

### Splitting Text Is Not the Same as Preserving Meaning

Fixed-size splitting is straightforward, but it can separate related information or break code examples.

I learned to use document structure whenever possible.

### Markdown Formatting Matters

Spaces, indentation, and newlines aren't always cosmetic.

For technical documentation, they may be essential to understanding or executing the content.

### Edge Cases Shape the Design

Handling oversized words, code fences, repeated headings, and empty documents gradually changed the architecture of the chunker.

### Metadata Is Part of Retrieval Design

Chunk IDs, heading paths, and source references aren't just extra fields.

They prepare the system for traceable search results and evidence-backed answers.

### Tests Help Validate Design Decisions

I learned that passing tests are useful, but the tests themselves must represent the intended behavior.

When a requirement changes, it's important to understand whether a failing test reveals a bug or an outdated expectation.

---

## 14. Current Limitations

The chunking pipeline is now functional, but there are still improvements I may explore later.

**Markdown parsing:** The implementation supports common heading and fenced-code patterns, but it isn't a complete CommonMark parser.

**Chunk size:** I'm currently using character counts. Embedding models operate on tokens, so I'll need to consider token-based limits later.

**Code fragments:** Oversized code blocks may produce fragments that aren't valid standalone Markdown or executable code.

**Heading preservation:** Headings are stored as metadata rather than fully preserved within each chunk's content.

**Incremental indexing:** Deterministic IDs are implemented, but document-change detection and efficient re-indexing are still future work.

For now, I want to keep the implementation understandable and avoid adding unnecessary complexity before building retrieval.

---

## 15. What's Next for DocPilot?

DocPilot can now:

- Discover and load Markdown documentation.
- Extract titles and source metadata.
- Identify Markdown sections and heading hierarchy.
- Recognize fenced code blocks.
- Split content into size-limited chunks.
- Preserve important formatting.
- Generate deterministic chunk IDs.
- Track related code fragments.
- Validate the pipeline using automated tests.

The next challenge is making these chunks searchable by meaning.

That brings me to **Part 4: Embeddings and Vector Representations**.

I'll explore how embedding models transform text into numerical vectors, how similarity between vectors works, and how to generate embeddings locally for DocPilot's document chunks.

After that, I'll begin integrating a vector database and building semantic retrieval.

The goal remains the same as when I started this project: build a local-first documentation assistant that produces useful, inspectable, evidence-backed results.

For now, the Markdown ingestion and chunking foundation is in place.

And I've learned that even a seemingly simple step like splitting documents can reveal a surprising amount about text processing, software design, and testing.

---

*This is Part 3 of my Building DocPilot series, where I'm learning about retrieval, embeddings, RAG, and AI systems by building a practical documentation assistant from scratch.*
