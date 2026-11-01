
from docpilot.ingestion.loader import load_markdown_files
from docpilot.ingestion.chunker import chunk_documents


# Step 1: Load Markdown documents
documents = load_markdown_files("examples/sample-docs")

print(f"\nDocuments loaded: {len(documents)}")


# Step 2: Generate chunks
chunks = chunk_documents(
    documents,
    max_size=1000,
    debug=False
)

print(f"Total chunks generated: {len(chunks)}")


# Step 3: Print all generated chunks
for chunk in chunks:
    print("\n" + "=" * 60)

    print(f"Title       : {chunk['title']}")
    print(f"Source      : {chunk['source']}")
    print(f"Heading     : {chunk['heading']}")
    print(f"Chunk Index : {chunk['chunk_index']}")
    print(f"Length      : {len(chunk['content'])} characters")

    print("-" * 60)
    print(chunk["content"])

print("\nChunking completed!")
