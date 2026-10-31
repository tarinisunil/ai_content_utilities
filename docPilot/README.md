# DocPilot

**A local-first documentation search and knowledge assistant — currently in planning.**

> **Project status: Planning / pre-v0.1.** DocPilot is not yet an implemented or production-ready application. The features and commands described below are goals unless explicitly marked as available.

DocPilot is an open-source engineering project to explore how conventional search, embeddings, hybrid retrieval, retrieval-augmented generation (RAG), and eventually bounded agentic workflows can make technical documentation easier to navigate and verify.

## Why DocPilot?

Technical knowledge often lives across Markdown guides, API references, architecture decisions, and runbooks. Exact keyword matching is valuable, but engineers may describe a problem differently from the terms used in documentation. LLM-generated answers can help summarize evidence, but they must remain traceable to the source.

DocPilot will investigate how to combine **lexical precision**, **semantic retrieval**, and **inspectable source references** without requiring a hosted service for core search.

## Goals

- Index local Markdown documentation while preserving headings, code blocks, and source locations.
- Support exact-term search and semantic search, then evaluate hybrid ranking.
- Return relevant passages with document paths and section references.
- Optionally generate grounded answers with citations and explicit uncertainty.
- Keep the core system local-first, low-cost, inspectable, and reproducible.
- Measure retrieval quality and performance rather than relying on demos.

## Proposed v0.1 architecture

```mermaid
flowchart TD
    A[Markdown files] --> B[Discovery and parsing]
    B --> C[Metadata and structure extraction]
    C --> D[Chunking]
    D --> E[Local embedding model]
    D --> F[SQLite FTS5 index]
    E --> G[ChromaDB vector index]
    Q[User query] --> H[Query processing]
    H --> F
    H --> E
    E --> G
    F --> I[Result fusion and ranking]
    G --> I
    I --> J[Passages with source references]
    J --> K[Optional LLM answer generation]
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the detailed proposed design and unresolved decisions.

## Planned technology stack

| Area | Initial candidate | Purpose |
| --- | --- | --- |
| Application | Python | Parsing, indexing, and search orchestration |
| Source format | Markdown | Version-controlled technical documentation |
| Lexical retrieval | SQLite FTS5 | Exact identifiers and keyword matching |
| Vector retrieval | ChromaDB | Semantic similarity search |
| Embeddings | Local model (TBD) | Offline-capable vector generation |
| Answer generation | Optional local or configured LLM | Evidence-backed synthesis |
| Interface | CLI first (planned) | Simple experimentation and evaluation |
| Tests/evaluation | Python tests + query dataset | Quality, latency, and regressions |

These are **proposed choices**, not validated benchmarks or installed dependencies.

## Roadmap

### v0.1 — Search and RAG (planned)

- [ ] Markdown discovery, parsing, and metadata extraction
- [ ] Structure-aware chunking and source mapping
- [ ] SQLite FTS5 indexing and lexical search
- [ ] Local embedding generation and ChromaDB indexing
- [ ] Hybrid retrieval and ranking experiments
- [ ] Source-linked results and optional cited answers
- [ ] Reproducible evaluation set and baseline metrics

### v0.2 — Documentation intelligence (exploratory)

- [ ] Duplicate and overlapping content detection
- [ ] Staleness and conflict signals with human verification
- [ ] Broken references and quality checks
- [ ] Incremental indexing and change handling

### v0.3 — Agentic workflows (exploratory)

- [ ] Evaluate agents against simpler deterministic workflows
- [ ] Read-only documentation investigation tools
- [ ] Human-reviewed documentation change proposals
- [ ] Tool permissions, auditability, and safety checks

## Getting started

**There is no working installation flow yet.** The initial implementation milestone is Markdown ingestion. Once code exists, this section will document prerequisites, installation, sample input, indexing, querying, and tests with verified commands.

To follow or contribute to the design today:

1. Read the [proposed architecture](ARCHITECTURE.md).
2. Review the roadmap above and identify assumptions worth testing.
3. Start with the Markdown ingestion milestone: file discovery, structural parsing, source references, and tests.
4. Capture each experiment's inputs, configuration, measurements, and limitations.

### Suggested repository layout (not yet implemented)

```text
docpilot/
├── README.md
├── ARCHITECTURE.md
├── src/docpilot/
├── tests/
├── examples/sample-docs/
├── benchmarks/
├── docs/decisions/
├── docs/experiments/
└── blog/
    ├── drafts/
    ├── engineering-log/
    └── assets/
```

## How success will be evaluated

Initial experiments should include representative questions with annotated relevant passages. Planned measurements include **Recall@k**, **MRR**, query latency, indexing time, memory use, and (for generated answers) citation support and faithfulness. No results are available yet.

## Engineering blog series

**Building DocPilot: From Documentation Search to Agentic Knowledge Systems** follows the project from proposed architecture through implementation, experiments, failures, and lessons learned.

- [Part 1 — Why I'm Building DocPilot](https://ai-content-utilties.hashnode.dev/why-i-m-building-docpilot-from-documentation-search-to-ai-powered-knowledge-systems)
- Part 2 (planned) — From Markdown Files to Searchable Documents

## Design principles

**Local-first · Inspectable retrieval · Evidence-backed answers · Low operational complexity · Open-source learning**

## Contributing and license

Contributing guidelines and a license have **not yet been selected**. Do not assume this repository has an open-source license until a `LICENSE` file is added. Contributions and public reuse will be governed by the license once chosen.

---

*DocPilot is a learning-driven engineering project. Planned capabilities will be updated as implementation and evaluation produce evidence.*
