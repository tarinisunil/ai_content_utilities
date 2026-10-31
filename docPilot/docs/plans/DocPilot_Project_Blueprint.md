# DocPilot — Project Blueprint & Context Recovery Guide

**Version:** 1.0  |  **Created:** 2026-10-24  |  **State:** Planning only

## 00 | Restart here

PROJECT IDENTITY: DocPilot — a local-first, MIT-licensed, self-hosted documentation search and knowledge assistant. Status as of 2026-10-24: planning complete; NO CODE, repository, benchmarks, or releases have been created in this conversation. Do not assume anything has been implemented.

USER GOAL: Build a practical tool that real developers and documentation teams can install and use. Learn document ingestion, chunking, embeddings, ChromaDB, similarity search, metadata filtering, hybrid retrieval, RAG, LLMs, and agentic workflows through implementation. Publish a transparent engineering blog series; show failures and trade-offs.

SCOPE DECISION: v0.1 must be useful without agents. Start with local Markdown documentation folders, local embeddings, persistent ChromaDB, keyword search, grounded answers with citations, incremental indexing, a web UI, and Docker setup. v0.2 adds documentation intelligence and PDF/HTML. v0.3 adds bounded LangGraph agent workflows.

NEXT ACTION: Create the repository skeleton, original sample documentation corpus, and executable vertical slice: ingest one Markdown folder -> normalize -> heading-aware chunk -> embed -> ChromaDB -> search CLI/API. Add tests and write first engineering log before implementing RAG.

HANDOFF INSTRUCTION FOR FUTURE ASSISTANT: Treat this document as the project source of truth, but ask for any newer repo/files or status log before changing code. Never claim implementation is complete based only on this plan. Preserve the MIT/open-source, local-first, inspectable retrieval, low-cost, content-system-neutral principles. Proceed in small runnable milestones and update the status section after each one.

## 01 | Product and users

PRODUCT: DocPilot. Working tagline: “Your documentation, searchable and intelligent.” The name is provisional; check name and trademark conflicts before public release.

PROBLEM: Engineering documentation lives across Markdown files, API references, runbooks and architecture decisions. Keyword-only search misses paraphrases, while naive LLM chat can invent answers and hide evidence.

PRIMARY USER: A maintainer of a Markdown-based technical documentation repository. SECONDARY USERS: technical writers, developer enablement teams, small engineering teams, and self-hosting enthusiasts.

CORE JOB: Point DocPilot at a folder of documentation, index it, ask a natural-language question, see relevant passages and a grounded answer with clickable source citations; update documents without rebuilding everything.

NON-GOALS FOR v0.1: SaaS hosting, enterprise identity, arbitrary cloud connectors, autonomous edits, multi-tenant permission models, complex distributed infrastructure, guaranteed correctness, and unrestricted internet crawling.

DIFFERENTIATORS: local-first and provider-independent; structure-aware parsing; inspectable retrieval; source-first citations; documentation health features as later expansion.

## 02 | Versions and acceptance gates

v0.1 — INSTALLABLE KNOWLEDGE SEARCH: local Markdown folder ingestion; normalization; heading-aware chunking; local Sentence Transformers embeddings; ChromaDB persistence; SQLite FTS5 keyword retrieval; semantic/keyword/hybrid retrieval; metadata filters; FastAPI endpoints; React/Vite search and chat UI; optional Ollama or configurable hosted LLM; grounded answers and citations; reindex changed files and delete removed files; Docker Compose; tests and documentation.

RELEASE GATE: a new user can follow README, index at least 100 Markdown documents, search and inspect relevant passages, ask grounded questions with citations, see insufficient-evidence handling, update/delete files and reindex, restart without losing index, and run tests. Quality must be evaluated against a labeled corpus; no invented precision target is promised.

v0.2 — DOCUMENTATION INTELLIGENCE: HTML/PDF parsing; duplicate and near-duplicate detection; conflicting instructions; deprecated API mentions; version comparisons; documentation health report. Every flag must show supporting evidence and allow human review.

v0.3 — AGENTIC ASSISTANT: bounded tool-using workflow with semantic_search, keyword_search, filtered_search, fetch_document, compare_sources, and evidence assessment. Read-only by default. Any proposed write requires explicit user approval. Compare against standard RAG before claiming benefits.

BACKLOG: Git repository connector, access-controlled multi-user mode, scheduled sync, pluggable content adapters, broader language support, exportable reports. These are not v0.1 promises.

## 03 | Architecture and flows

INDEX PIPELINE: source folder -> discovery and content hashes -> Markdown parser -> normalized document (ID, path, title, headings, content, metadata) -> heading-aware chunks with offsets and parent IDs -> embedding model -> ChromaDB upsert; separately populate SQLite document registry and FTS5 text index.

QUERY PIPELINE: user query + validated filters -> query embedding + keyword query -> ChromaDB similarity retrieval and SQLite FTS5 retrieval -> reciprocal-rank fusion or a documented alternative -> optional reranker -> top passages -> evidence sufficiency check -> prompt assembly with source IDs -> LLM -> cited answer -> citation validation -> UI.

AGENT PIPELINE (v0.3): route query -> choose bounded search tools -> inspect results -> optionally fetch or compare -> stop on evidence sufficiency or step budget -> grounded synthesis; log tool trace. No unconstrained recursion.

BOUNDARIES: loaders, chunkers, embedding providers, vector store adapter, retrieval, answer generation, and agent graph are separate interfaces. Do not hide core indexing/retrieval behind an orchestration framework. Use LangGraph only for agent orchestration.

STORAGE: ChromaDB for vectors and chunk text; SQLite for file registry, hashes, ingestion state, keyword index, and optional evaluation history. Both persist under a configured data directory. Do not commit real user documents or persisted databases.

## 04 | Data contracts and metadata

Document: document_id (stable hash of normalized source path within source namespace), source_id, relative_path, source_uri, title, content_type, language, version (optional), tags, updated_at (optional), content_hash, extracted_text, sections.

Chunk: chunk_id (stable document_id + strategy_version + index/content fingerprint), document_id, chunk_index, heading_path, text, token_count, char_start/end if available, metadata, embedding_model_id, embedding_version.

ChromaDB: ids = chunk IDs; documents = chunk text; embeddings = generated numeric vectors; metadatas = flat supported scalar fields such as document_id, source_id, path, section, version, content_type, language, category. Normalize missing values deliberately; do not store nested objects as metadata.

FILTER CONTRACT: typed allowlisted filters (source_id, path prefix handled outside Chroma if needed, version, content_type, category, language). Compose Chroma where clauses using supported operators; validate inputs before executing.

CITATION: source document ID, path/URI, section/heading, chunk ID, optional text span. UI citation opens a source preview and, where possible, the original file. An LLM citation is not accepted as valid unless the referenced chunk was actually supplied in the context.

INDEX COMPATIBILITY: persist embedding model name, revision, vector dimensionality, distance metric, chunking configuration, and index schema version. A model or incompatible chunking change triggers a new collection/reindex, not silent mixing.

## 05 | Retrieval and RAG design

CHUNKING EXPERIMENTS: baseline fixed-character or token chunks; recursive splitting; heading-aware Markdown chunks. Preserve code fences, tables and heading context where possible. Record chunk size and overlap; start with approximately 400–700 tokens and 50–100 overlap as hypotheses, then evaluate. Avoid duplicating too much content.

EMBEDDINGS: initial local model sentence-transformers/all-MiniLM-L6-v2 (lightweight English baseline). Compare a stronger retrieval model such as BAAI/bge-small-en-v1.5 only after baseline evaluation. Verify model licenses and model-specific query instructions. Never equate cosine distance with probability.

VECTOR RETRIEVAL: Chroma persistent collection; cosine distance configuration; top-k candidates; metadata filters; deterministic response schema with raw distances, not invented confidence percentages.

KEYWORD RETRIEVAL: SQLite FTS5 with documented tokenization and BM25 ordering; crucial for error codes, endpoint names, and exact symbols. Hybrid fusion via reciprocal rank fusion; tune using labeled questions. Optional cross-encoder reranking later.

RAG: system instruction requires evidence-grounded answers; include source chunks with explicit IDs, bounded context, and a safe insufficient-evidence response. Treat retrieved content as untrusted data, not instructions. Validate citation IDs and show excerpts. A missing or contradictory source must be surfaced, not hidden.

LLM PROVIDERS: optional local Ollama for no cloud account; configurable hosted provider behind interface. Search must still work with LLM disabled. Document local hardware requirements and model download sizes after choosing actual model.

## 06 | API and UI contract

INITIAL API: POST /api/sources/local (register allowed local documentation folder; reject arbitrary server path traversal), POST /api/index (trigger/reconcile indexing), GET /api/index/status, POST /api/search (query, mode, filters, top_k), POST /api/chat (question, filters, provider), GET /api/documents/{id}, GET /api/health. Version endpoints or use /api/v1 before public compatibility commitments.

SEARCH RESPONSE: query, mode, applied_filters, results [{chunk_id, document_id, title, path, section, excerpt, score_type, score, rank}], elapsed_ms, index_version. Distinguish distance from fused rank.

CHAT RESPONSE: answer, citations [{chunk_id, document_id, path, section, excerpt}], evidence_status (sufficient/insufficient/conflicting), model, latency, retrieval_trace_id. Streaming optional after basic endpoint works.

UI PAGES: setup/source selection, indexing status, search results with filters and source previews, ask/chat with inline citations, retrieval inspector (debug view), settings/provider status. Show empty/error/loading states. Never require an LLM just to use search.

SECURITY: v0.1 is single-user localhost deployment. Bind services to localhost by default, validate source roots, constrain file access, sanitize rendered Markdown/HTML, avoid logging secrets, and do not expose a public instance without authentication and a threat-model review.

## 07 | Repository blueprint

docpilot/

  app/api/               FastAPI routes, request/response schemas

  app/ingestion/         source scanner, Markdown loader, normalizer, sync

  app/chunking/          fixed, recursive, heading-aware strategies

  app/embeddings/        provider interface and local model

  app/vectorstore/       Chroma adapter and collection management

  app/retrieval/         vector, FTS5, fusion, filters, reranking

  app/rag/               prompt assembly, generation, citation checks

  app/agents/            reserved for v0.3 LangGraph graph and tools

  app/storage/           SQLite registry and migration scripts

  app/evaluation/        retrieval and answer evaluation

  ui/                    React + Vite application

  tests/                 unit, integration, end-to-end fixtures

  data/sample_docs/      original fictional sample docs

  evaluations/           labeled questions and results

  experiments/           reproducible comparisons

  blog/                  draft posts and experiment logs

  docs/                  architecture, ADRs, setup, security

  docker-compose.yml, Dockerfile, pyproject.toml, .env.example, README.md, LICENSE

CI: lint, type checks where practical, pytest, UI build, and a small deterministic smoke test. Pin dependency versions for reproducibility; refresh them deliberately.

## 08 | Milestones and tasks

M0 — PROJECT FOUNDATION: initialize repository, MIT LICENSE, README, contribution guide, pyproject, configuration, test framework, original sample corpus, architecture decision records. Done when setup and tests run on a clean machine.

M1 — INDEXING VERTICAL SLICE: scan Markdown folder, parse and normalize, heading-aware chunk, local embedding, persist in Chroma, build simple search CLI, test chunk and source mapping. Done when indexed docs survive restart and return inspectable chunks.

M2 — RETRIEVAL: add SQLite FTS5, filters, hybrid rank fusion, stable API contracts, search UI, index reconciliation for edits/deletes, failure recovery. Done when a user can search and filter a real folder and update the index.

M3 — RAG: add optional Ollama adapter, grounded prompting, citation validation, source previews, abstention behavior, chat UI, negative tests. Done when answers cite only supplied sources and no-LLM search remains functional.

M4 — RELEASE HARDENING: Docker Compose, clear install docs, migration/version checks, structured logging, privacy/security review, 100+ document trial, onboarding test with a second user, tagged v0.1 release.

M5 — DOC INTELLIGENCE (v0.2): add duplicate detection, conflict candidates, version comparisons, PDF/HTML; provide evidence and review workflow.

M6 — AGENTS (v0.3): LangGraph with search/fetch/compare tools, iteration/time/token budgets, traces, human approval for any changes, and head-to-head evaluation against fixed RAG.

IMPLEMENTATION RULE: ship each milestone with code, tests, evaluation notes, README updates, and at least one blog artifact. Avoid starting M6 before M3 and baseline evaluation work.

## 09 | Evaluation and reliability

DATASET: start with 15–20 labeled queries for M1; expand to 50 by M3 and 100–150 for mature comparisons. Include exact-term lookups, paraphrases, multi-section answers, metadata-constrained queries, unanswerable questions, conflicting documents, and stale/changed documents. Store expected relevant document/chunk IDs and reference answers where feasible.

RETRIEVAL METRICS: Recall@5, MRR@10, nDCG@10 when graded labels exist, filter correctness, query latency. Evaluate fixed, heading-aware, vector, keyword, and hybrid variants on the same corpus.

GENERATION METRICS: factual correctness using human-reviewed reference answers, citation support, abstention on unanswerable queries, contradiction handling, token usage, latency, and cost where applicable.

AGENT METRICS: compare answer quality, tool-call count, wall-clock latency, and provider cost against fixed RAG. Include tool failures and budget-exhaustion cases.

ROBUSTNESS TESTS: malformed Markdown, empty files, duplicates, encoding problems, huge files, fenced code, tables, path traversal, malicious prompt instructions embedded in docs, missing providers, corrupt index, changed/deleted documents, conflicting versions, and restart recovery.

RELEASE REPORT: include corpus size, embedding model and revision, chunk strategy, vector metric, LLM and version, hardware, test questions, actual scores, known failures. Never present unmeasured targets as achieved results.

## 10 | Licensing, privacy, distribution

LICENSE: MIT for original DocPilot code, with copyright holder/year filled in by repository owner. MIT permits commercial use and modification with preservation of copyright/license notices; it does not relicense third-party code, datasets, or model weights.

CHECK BEFORE RELEASE: dependency licenses, embedding/LLM model licenses and redistribution terms, sample content licenses, brand/trademark availability, generated assets and attribution requirements. Keep a THIRD_PARTY_NOTICES file if needed.

PRIVACY: index data stays local by default; Ollama mode should not send docs to hosted LLMs. Clearly label hosted-provider configuration and what content is transmitted. Do not commit private docs, vector databases, API keys, logs containing source text, or secrets.

DEPLOYMENT: localhost-first Docker Compose, persistent volumes, health checks, pinned images where feasible, simple uninstall/data deletion instructions. Security guidance must warn that publicly exposed instances require authentication, authorization, network controls, and further review.

COMMUNITY: CONTRIBUTING.md, issue templates, sample dataset, reproducible bug report instructions, release changelog, code of conduct optional.

## 11 | Blog and learning workflow

SERIES TITLE: “Building a Content Knowledge Engine: From Embeddings to Agentic RAG.” Positioning: practical, low-cost, open-source, content-system-neutral engineering experiments; show failures and trade-offs, not just polished demos.

POSTS: (1) Why DocPilot instead of another chatbot; (2) Markdown ingestion and chunking; (3) Embeddings and similarity; (4) ChromaDB metadata filtering and updates; (5) Hybrid search vs vector-only; (6) Grounded RAG and citations; (7) Hallucinations and evaluation; (8) Tool-using agents with LangGraph; (9) Agentic vs standard RAG results; (10) Shipping an MIT-licensed self-hosted tool; (11) documentation health intelligence.

REUSABLE POST FORMAT: real problem; what I wanted to learn; architecture/decision; what I built; reproduction steps; what worked; what failed; measured results; trade-offs; next experiment. Link to tagged commit/release and actual data.

SUSTAINABILITY: after each 60–90 minute coding session write three lines in blog/LEARNING_LOG.md: attempted, result, next step. Publish a short experiment note even if the full feature is unfinished. Do not delay writing until release.

BLOG FOUNDATION: author has 15 years of customer-focused engineering experience in content systems and structured data, wants practical AI utilities rather than flashy demos, values structure, consistency, reliability, low cost, and honest failure analysis.

## 12 | Decision log and open questions

DECIDED: local-first; MIT for own code; Python/FastAPI; React/Vite; local Sentence Transformers; ChromaDB; SQLite FTS5; optional Ollama; LangGraph only for v0.3; Markdown-first; inspectable citations; no automatic documentation writes; GitHub-friendly reproducibility.

PROVISIONAL: project name DocPilot; Python version 3.12+; initial embedding model all-MiniLM-L6-v2; chunk sizes; vector distance configuration; Ollama model; UI layout; release timeline. Validate with experiments, compatibility and hardware.

OPEN QUESTIONS (NOT BLOCKERS FOR M0): target OS (Mac/Linux/Windows), expected CPU/RAM, primary documentation corpus, whether Git repository synchronization is required soon, intended public demo hosting, user’s preferred publishing platform, model download size tolerance, and whether the repo already exists.

ASSUMPTIONS: single-user localhost in v0.1; English-first; Markdown source folder; low-cost/free tools; no private data shared; one contributor initially. Ask before changing these if actual user requirements differ.

STATUS AS OF DOCUMENT CREATION: all milestones NOT STARTED; no repository URL, code, benchmark results, license file, or deployed service exists based on this conversation.

## 13 | Session restart template

When starting a new conversation, upload this file and say:

“Continue DocPilot using this blueprint as the source of truth. First summarize the product, current milestone, completed work, decisions and next three concrete actions. I will provide any newer repo or progress notes. Do not assume planned work is implemented. Then help me complete the next runnable milestone with tests and update the handoff log.”

At the end of EVERY future session, update the following fields in this document or a companion STATUS.md:

DATE / MILESTONE / REPO URL OR ARCHIVE / COMMIT HASH / IMPLEMENTED & VERIFIED / TEST COMMANDS AND RESULTS / CHANGED DECISIONS / KNOWN ISSUES / NEXT THREE ACTIONS / BLOG NOTES.

INITIAL STATUS ENTRY — 2026-10-24: Planning only. Next three actions: (1) create repo and original sample corpus; (2) implement Markdown loader + normalization + heading-aware chunker; (3) integrate local embeddings and persistent Chroma search with unit tests. No tests have been run.

RESTART SAFETY: if newer code or status contradicts this plan, inspect the newer evidence and propose a documented decision update; do not overwrite working implementation based solely on this blueprint.

