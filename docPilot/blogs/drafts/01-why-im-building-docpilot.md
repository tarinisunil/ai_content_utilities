# Why I'm Building DocPilot: From Documentation Search to AI-Powered Knowledge Systems

*Building DocPilot — Part 1 | Architecture, Motivation, and Engineering Goals*

Software engineering has a documentation problem.

Not necessarily because documentation doesn't exist, but because finding the right information becomes increasingly difficult as systems grow.

A small project might have a README, a few configuration files, and some API documentation. A mature engineering system can have hundreds of Markdown files, architecture decision records (ADRs), API specifications, troubleshooting guides, and operational runbooks distributed across multiple repositories.

The information is often there. The challenge is finding it, understanding its context, and determining whether it answers the question we're asking.

This is the problem I want to explore with **DocPilot**, a local-first, self-hosted documentation search and knowledge assistant.

**DocPilot is currently a planned system, not a completed product.** I haven't built the retrieval pipeline or validated the proposed architecture yet. This article describes why I'm starting the project, the technical decisions I'm considering, and what I want to learn along the way.

More importantly, this project is an opportunity to explore modern information retrieval, embeddings, retrieval-augmented generation (RAG), and eventually AI agents through actual engineering work.

---

## 1. The Problem I'm Trying to Solve

Consider a typical engineering scenario.

A service starts returning errors whenever a downstream dependency becomes unavailable. An engineer wants to understand how the system handles that failure.

They search the documentation for:

> What happens when the payment service becomes unavailable?

But the relevant documentation might be titled **Circuit Breaker Configuration and Retry Policies**.

It might contain details about failure thresholds, timeouts, fallback behavior, and dependency health checks without ever using the exact phrase from the engineer's question.

Traditional keyword search can struggle here.

Tools such as `grep`, `ripgrep`, and full-text search engines are extremely useful when we know the terminology we're looking for. They're fast, predictable, and easy to understand.

But technical questions don't always match the vocabulary used in the documentation.

### Vocabulary mismatch

An engineer searches for "service unavailable," while the documentation describes "circuit breaker open state." Both refer to related concepts, but a keyword-based system may not recognize that relationship.

### Fragmented knowledge

Information about a single feature might be distributed across multiple documents. An architecture document explains the design, an API reference describes the interface, and a runbook explains operational behavior. Finding one relevant file doesn't necessarily provide the complete answer.

### Documentation structure

Markdown files aren't just plain text. They contain headings, nested sections, tables, code blocks, configuration examples, and links. A search system that treats every document as an unstructured string may lose relationships that are important for understanding the content.

### Trust and traceability

Even when an AI assistant produces a convincing answer, an engineer still needs to know:

- Which document supports this answer?
- Which section contains the relevant information?
- Is the answer grounded in the documentation?
- What happens when the documentation doesn't contain enough evidence?

For engineering documentation, a plausible answer isn't necessarily a correct answer.

**The goal isn't simply to make documentation searchable. It's to make the right information easier to retrieve, inspect, and verify.**

---

## 2. Why I Want to Build This

Embeddings, vector databases, RAG, and AI agents have become common topics in modern software engineering.

There are plenty of tutorials demonstrating how to load documents, generate embeddings, store them in a vector database, and ask questions using a language model. Those examples are useful for understanding the basic workflow.

But I'm interested in the engineering questions that appear once we move beyond a small demonstration.

**How should documents be chunked?** A fixed-size text splitter is simple to implement, but what happens when it separates a configuration example from the heading that explains it?

**How reliable is semantic search?** Embeddings can capture conceptual similarity, but will they retrieve an exact error code, environment variable, or API parameter as reliably as keyword search?

**Do we always need an LLM?** If a search system can return the correct document section with enough context, generating a natural-language answer might not always be necessary.

**How do we measure retrieval quality?** A handful of successful queries can make a demo look impressive. That doesn't tell us how the system behaves across different document types, query patterns, or failure scenarios.

**Where do agents actually help?** Can tool-using workflows solve documentation maintenance problems that are difficult to handle with a conventional retrieval pipeline? Or would a deterministic workflow be simpler and more reliable?

I'm approaching DocPilot as a software engineering project rather than an AI tutorial. The objective is to build a useful system while developing a deeper understanding of the technologies, their limitations, and the architectural trade-offs involved.

---

## 3. What Is DocPilot?

**DocPilot is a planned local-first, open-source documentation search and knowledge assistant.**

The initial idea is straightforward: give DocPilot a directory of technical documentation, let it build a searchable index, and allow engineers to retrieve relevant information using natural-language queries or exact technical terms.

Over time, I want to explore whether the same foundation can support documentation analysis and controlled agentic workflows.

### What I want the first version to do

The initial version, DocPilot v0.1, will aim to:

1. Read Markdown files from a local directory.
2. Extract content while preserving useful document structure.
3. Divide documents into meaningful chunks.
4. Generate embeddings for semantic retrieval.
5. Build a keyword search index.
6. Combine lexical and semantic search results.
7. Return relevant passages with source references.
8. Optionally generate answers using an LLM, grounded in retrieved evidence.

The word *optionally* matters. I don't want DocPilot to depend on an LLM for every interaction. Search should remain useful even when answer generation is disabled.

### What DocPilot is not

At least initially, DocPilot is not intended to be:

- A replacement for GitHub, documentation websites, or existing documentation platforms.
- A general-purpose chatbot trained on private documentation.
- A fully autonomous agent capable of modifying repositories.
- A production-ready enterprise knowledge platform.

I want to start with a focused problem and expand the system only when the engineering evidence justifies doing so.

---

## 4. The Initial Architecture

My current plan is to build DocPilot primarily in Python.

The first architecture will have two major workflows: **document indexing** and **query processing**.

### Document indexing

The indexing pipeline will transform Markdown files into searchable representations.

```text
Markdown Files
      |
      v
File Discovery
      |
      v
Markdown Parsing
      |
      v
Metadata Extraction
      |
      v
Document Chunking
      |
      +----------------------+
      |                      |
      v                      v
Embedding Generation    Text Indexing
      |                      |
      v                      v
   ChromaDB              SQLite FTS5
```

The first challenge will be extracting useful information from Markdown without destroying its structure.

For example, consider:

````markdown
# Payment Service

## Retry Configuration

The service retries failed requests
using exponential backoff.

```yaml
retry:
  max_attempts: 3
  backoff_ms: 500
```
````

The heading, explanatory text, and configuration example belong together conceptually. A naive text splitter might separate them into different chunks.

If that happens, a retrieval system could return the configuration without the explanation needed to interpret it.

This is one reason I want to investigate structure-aware chunking rather than assuming that fixed-size chunks are sufficient.

### Query processing

Once the documents are indexed, DocPilot will need to retrieve useful information in response to a query.

```text
         User Query
              |
              v
       Query Processing
              |
       +------+------+
       |             |
       v             v
   SQLite FTS5    Embedding Model
       |             |
       v             v
  Keyword Search  Vector Search
       |             |
       +------+------+
              |
              v
       Result Fusion
              |
              v
       Ranked Passages
              |
       +------+------+
       |             |
       v             v
  Search Results   Optional LLM
       |             |
       v             v
  Source Links    Grounded Answer
                  + Citations
```

This is a conceptual architecture, not an implemented pipeline. I expect some of these components to change as I experiment.

---

## 5. Why These Technologies?

One of my goals is to keep the initial architecture small enough to understand and operate locally. I'm deliberately avoiding unnecessary infrastructure until I have a reason to introduce it.

### Python for the application

Python is a practical choice because of its ecosystem for document processing, embeddings, vector databases, and language model integration. It should allow me to spend more time investigating retrieval behavior and less time building infrastructure around the experiments.

### Markdown as the first document format

Markdown is widely used for technical documentation and fits naturally into Git-based engineering workflows.

It's also an interesting format for retrieval experiments because its structure carries meaning. Headings, lists, code fences, and links are not merely formatting details. They often define the relationships between technical concepts.

Starting with Markdown will let me explore these challenges without immediately introducing PDF extraction, OCR, or complex document conversion.

### SQLite FTS5 for keyword search

SQLite includes FTS5, a full-text search extension. I want to use it as the lexical retrieval component.

Keyword search remains particularly valuable for technical content containing exact identifiers, including:

- Error codes
- Configuration keys
- API endpoint names
- Class and function names
- Environment variables

Semantic similarity isn't necessarily the best approach for every type of query. SQLite also supports the local-first direction without requiring a separate search server.

### ChromaDB for vector retrieval

ChromaDB is my initial choice for storing and querying document embeddings.

I want to explore how vector similarity performs on technical documentation, especially when queries use different wording from the source material.

I'm not treating ChromaDB as the universally best vector database. It's a reasonable starting point for experimentation, and I can revisit the decision if the requirements change.

### Embedding models

An embedding model converts text into numerical representations that can be compared using similarity measures.

The basic idea is that semantically related passages may have similar vector representations even when they don't share the same keywords.

However, I don't want to assume that all embedding models behave equally well on technical documentation.

I plan to compare models based on retrieval relevance, latency, resource consumption, and performance on domain-specific terminology. The initial preference is a locally executable model, consistent with the project's local-first goals.

### Optional LLM-based answers

Once retrieval is working reliably, I want to experiment with using an LLM to synthesize answers from retrieved passages.

This is where retrieval-augmented generation comes in. Rather than relying only on information encoded in the model's parameters, a RAG system supplies relevant external context during answer generation.

But RAG doesn't automatically guarantee correctness. If retrieval misses an important passage, the answer may be incomplete. If the model interprets the context incorrectly, it may still produce unsupported statements.

That's why I want the system to expose citations and preserve access to the original source material.

---

## 6. Why Hybrid Search?

One architectural choice I want to investigate early is combining keyword search with semantic retrieval.

Consider two queries.

**Query A:**

> What does PAYMENT_RETRY_MAX_ATTEMPTS control?

This contains an exact configuration identifier. Keyword search may be highly effective.

**Query B:**

> How does the system avoid repeatedly calling an unhealthy downstream service?

This describes behavior without necessarily using the terminology found in the documentation. Semantic search may be more useful here.

A hybrid system can use both retrieval methods and combine their results.

One possible approach is Reciprocal Rank Fusion (RRF), which combines ranked lists without requiring their raw scores to share the same scale.

However, whether hybrid search improves results will depend on the document collection and query distribution.

I want to compare three configurations:

1. Keyword search only.
2. Semantic search only.
3. Hybrid keyword and semantic search.

Rather than declaring a winner based on intuition, I'll evaluate them against the same query set.

This comparison should help establish when the additional complexity of hybrid retrieval is justified.

---

## 7. How I Plan to Measure Success

One thing I want to avoid is building a system that looks impressive in a demo but has no measurable quality baseline.

Before adding too many features, I plan to create a small evaluation dataset.

It will contain technical questions, expected relevant documents or passages, and different categories of search behavior.

Some queries will use exact identifiers. Others will use natural language, abbreviations, or terminology different from the source documents.

I'll initially focus on the following measurements.

| Metric | What it tells me |
|---|---|
| Recall@k | Whether relevant passages appear in the top k results |
| MRR | How highly the first relevant result is ranked |
| Query latency | How long retrieval takes |
| Indexing time | The cost of processing the documentation |
| Memory usage | The resources required to operate locally |
| Citation accuracy | Whether generated answers correctly reference supporting passages |

For generated answers, I also want to evaluate whether claims are supported by the retrieved evidence.

Importantly, these are planned measurements.

**I don't have benchmark results yet.**

As the project progresses, I intend to publish the actual measurements, configurations, and relevant implementation details. I also want to document cases where an approach performs worse than expected.

Those failures are often more informative than successful demonstration queries.

---

## 8. Design Principles

There are a few principles I want to maintain throughout the project.

### Local-first

DocPilot should be able to index and search documentation locally without requiring external APIs. Optional hosted models or integrations may be explored later, but they shouldn't be mandatory for the core search workflow.

### Inspectable results

The system should return more than an answer. Users should be able to inspect the source document, section, and passage that contributed to a result.

### Evidence-backed answers

If an LLM generates an answer, that answer should be tied to retrieved evidence. When sufficient evidence isn't available, the system should acknowledge the limitation rather than inventing an explanation.

### Low operational complexity

I want to avoid introducing services that aren't necessary for the current requirements. SQLite, local embeddings, and a lightweight application architecture are attractive starting points because they reduce operational overhead.

### Open-source and reproducible

I plan to develop DocPilot openly and document its design decisions, experiments, and limitations. Where practical, experiments should include the dataset, configuration, commands, and measurements needed for reproduction.

---

## 9. The Development Roadmap

I plan to develop DocPilot in three phases. These are proposed milestones rather than commitments to a fixed feature set.

### v0.1 — Search and RAG

The first phase will focus on building a reliable retrieval foundation.

Planned capabilities include:

- Markdown ingestion and metadata extraction
- Structure-aware document chunking
- Local embedding generation
- Keyword search with SQLite FTS5
- Vector retrieval with ChromaDB
- Hybrid search and result ranking
- Source references and citations
- Optional LLM-based answer generation
- Retrieval evaluation and performance measurements

The main question for this phase is:

**Can DocPilot consistently retrieve the right technical information and make the results easy to verify?**

### v0.2 — Documentation Intelligence

Once retrieval is reliable, I want to investigate whether the system can help identify problems within the documentation itself.

Potential experiments include duplicate content detection, stale documentation signals, conflicting descriptions, broken references, and missing coverage.

These problems are more difficult than ordinary search. For example, two documents can describe different configurations without necessarily contradicting each other. A document can be old without being incorrect.

Any analysis will need to account for that uncertainty.

The question for this phase is:

**Can retrieval techniques help engineers identify documentation quality problems without generating excessive false positives?**

### v0.3 — Agentic Workflows

The final planned phase is an exploration of AI agents and tool-using workflows.

I'm particularly interested in bounded tasks such as investigating documentation inconsistencies, gathering supporting evidence across files, and proposing documentation changes.

I don't want to introduce an agent simply because agents are popular. I'll first investigate whether a deterministic workflow can solve the problem.

If an agent is justified, its tools, permissions, actions, and outputs should remain inspectable. Any proposed file modifications should be reviewable before they are applied.

The central question will be:

**Where does agentic behavior provide measurable value over simpler retrieval and automation workflows?**

---

## 10. Trade-offs, Unknowns, and Limitations

Even before implementation, there are several uncertainties worth acknowledging.

**Chunking may become more complicated than expected.** Technical documentation mixes prose, code, tables, and hierarchical sections. A strategy that works for one document type may perform poorly on another.

**Embeddings may not handle exact technical identifiers reliably.** This is one reason lexical retrieval remains part of the proposed architecture.

**Hybrid retrieval introduces ranking complexity.** Combining results from different retrieval systems requires careful evaluation and may not always improve relevance.

**Local-first introduces resource constraints.** Embedding models and local language models consume memory and compute resources. The system will need to balance model quality with practical operating requirements.

**Citations do not automatically guarantee correctness.** An answer can cite a real document while misinterpreting what it says. Evidence quality and answer faithfulness must be evaluated separately.

**Documentation quality limits answer quality.** Retrieval cannot reliably resolve information that is missing, outdated, or contradictory without additional evidence.

These aren't reasons to avoid building the system. They're exactly the kinds of engineering questions that make the project interesting.

---

## 11. What Comes Next: Markdown Ingestion

The first implementation milestone will be building a Markdown ingestion pipeline.

Before embeddings, vector databases, or RAG, DocPilot needs a reliable way to transform documentation files into structured records.

I'll start by investigating how to:

1. Discover Markdown files recursively.
2. Read and validate file content.
3. Extract document-level metadata.
4. Preserve heading hierarchy.
5. Identify code blocks and other structural elements.
6. Produce records with traceable source locations.
7. Handle malformed files and ingestion errors.
8. Write tests for the ingestion pipeline.

I'll also start collecting representative Markdown examples that can serve as a reproducible test corpus.

Once ingestion is working, the next challenge will be chunking: deciding which parts of a document should be grouped together for indexing and retrieval.

That decision will influence nearly everything that follows.

The next article in the series will be:

**Part 2 — From Markdown Files to Searchable Documents: Building DocPilot's Ingestion Pipeline**

I'll walk through the implementation, the design alternatives, the problems encountered, and the initial results.

---

## Final Thoughts

DocPilot is starting with a relatively simple idea: make technical documentation easier to search and understand.

But behind that idea are several interesting engineering problems involving document structure, information retrieval, semantic similarity, ranking, evaluation, and trustworthy answer generation.

I'm not starting with the assumption that an LLM is the solution to every documentation problem.

In some cases, keyword search may be sufficient. In others, semantic retrieval might help. Hybrid search may provide better coverage, while RAG could make retrieved information easier to consume.

And agentic workflows may eventually prove useful for tasks that require multiple steps and tools.

The point is to investigate these possibilities through implementation and measurement rather than assumptions.

**I want DocPilot to be more than a project that demonstrates how RAG works. I want it to be a record of the engineering decisions, experiments, failures, and lessons involved in building a useful AI-assisted documentation system.**

This is the first step.

*Next in the series: From Markdown Files to Searchable Documents — Building DocPilot's Ingestion Pipeline.*
