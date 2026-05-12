# 📄 Hierarchical Document Intelligence Pipeline

A hybrid NLP + LLM pipeline for reconstructing document structure from DOCX files.

This project extracts hierarchical sections, annotates them with semantic metadata, computes confidence scores, and visualizes the results through an interactive Streamlit interface.

---

# 🚀 Features

## ✅ Hierarchical Structure Reconstruction
- Detects headings and section nesting
- Rebuilds document hierarchy
- Preserves section relationships

## ✅ Hybrid NLP + LLM Pipeline
- Rule-based structure parsing
- LLM-powered semantic annotation
- Deterministic chunking + validation

## ✅ Semantic Section Annotation
Each section is enriched with:
- section type
- keywords
- confidence
- notes

## ✅ Confidence Scoring
Confidence is computed using:
- text coverage
- annotation quality
- hierarchy quality
- structural consistency

## ✅ Table Extraction
Supports:
- DOCX tables
- row serialization
- table-aware chunking
- table rendering in Streamlit

## ✅ Interactive UI
Streamlit dashboard includes:
- document summary
- hierarchy tree
- section explorer
- confidence heatmap
- failure visualization
- rendered tables

## ✅ Evaluation Pipeline
Includes:
- sample documents
- expected outputs
- automated evaluation script

---

# 🧠 Why This Exists

Most document parsers flatten everything into plain text.

Real-world documents contain:
- hierarchy
- repeated sections
- inconsistent bullets
- missing headings
- noisy formatting
- tables

This project explores how hybrid systems (rules + LLMs) can reconstruct document structure more reliably.

---

# 🏗️ Architecture

```text
DOCX
  ↓
Block Extraction
  ↓
Hierarchy Reconstruction
  ↓
Flatten + Chunk
  ↓
LLM Annotation
  ↓
Merge
  ↓
Confidence Scoring
  ↓
Document-Level Summary
  ↓
Interactive Visualization
```

---

# 📂 Project Structure

```text
project/
│
├── app.py
├── ui.py
├── extractor.py
├── structure.py
├── chunker.py
├── merger.py
├── scorer.py
├── finalizer.py
├── schema.py
├── utils.py
├── llm.py
├── evaluate.py
│
├── samples/
│
├── README.md
├── requirements.txt

```

---

# 📄 File-by-File Breakdown

## `app.py`
Main CLI pipeline.

Responsible for:
1. extracting document blocks
2. reconstructing hierarchy
3. chunking sections
4. LLM annotation
5. merging results
6. confidence scoring
7. final document summarization
8. schema validation

Run:

```bash
python app.py samples/sample1.docx
```

Debug mode:

```bash
python app.py samples/sample1.docx --debug
```

---

## `ui.py`
Interactive Streamlit application.

Features:
- document upload
- hierarchy tree viewer
- section explorer
- confidence heatmap
- failure diagnostics
- structured JSON viewer
- rendered table visualization

Run:

```bash
streamlit run ui.py
```

---

## `extractor.py`
Extracts raw document blocks from DOCX files.

Detects:
- headings
- bullets
- paragraphs
- tables
- soft headings (heuristic)

---

## `structure.py`
Builds hierarchical section trees.

Handles:
- heading nesting
- recursive structure
- tree rendering
- flattening for chunking

---

## `chunker.py`
Creates token-safe section chunks.

Preserves:
- hierarchy paths
- section boundaries
- section metadata
- serialized table content

---

## `utils.py`
Prompt construction + JSON extraction utilities.

Handles:
- strict annotation prompts
- malformed JSON recovery
- parsing safeguards

---

## `llm.py`
LLM interface layer.

Supports two providers, switchable via env var, CLI flag, or UI toggle:
- **OpenRouter** — cloud-hosted models via `https://openrouter.ai/api/v1`
- **Ollama** — local models via `http://localhost:11434/v1`

Exposes `configure_provider(provider, model)` for runtime switching.

---

## `merger.py`
Combines chunk-level outputs into a unified document.

Handles:
- keyword merging
- confidence aggregation
- metadata normalization

---

## `scorer.py`
Computes document confidence scores.

Signals include:
- coverage
- hierarchy depth
- annotation quality
- section confidence

---

## `finalizer.py`
Runs a final document-level LLM pass.

Generates:
- title
- summary
- document type
- global keywords

---

## `schema.py`
Pydantic schemas for:
- content blocks
- sections
- hierarchical documents
- table-aware blocks

---

## `evaluate.py`
Automated evaluation script.

Validates:
- hierarchy depth
- section count
- summary generation
- document classification

Run:

```bash
python src/evaluate.py
```

---

# 🧪 Sample Documents

The `samples/` folder contains:
- clean research-style documents
- engineering proposals
- meeting notes
- intentionally messy documents
- table-heavy documents

These are used for evaluation and failure testing.

---

# ⚙️ Installation

## 1. Clone the repo

```bash
git clone <repo-url>
cd <repo-name>
```

---

## 2. Create virtual environment

```bash
python -m venv .venv
```

Activate:

### macOS/Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create `.env`:

```env
# Required for OpenRouter
OPENROUTER_API_KEY=your_key_here

# Provider selection: "openrouter" (default) | "ollama"
LLM_PROVIDER=openrouter

# Per-provider model overrides (optional)
OPENROUTER_MODEL=openai/gpt-oss-20b:free
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434/v1
```

---

# 🤖 LLM Providers

The pipeline supports **OpenRouter** and **Ollama** interchangeably. All three surfaces (env, CLI, UI) are equivalent — they all call `configure_provider()` before inference starts.

## OpenRouter (default)

Requires `OPENROUTER_API_KEY` in `.env`. Uses any model available on OpenRouter.

## Ollama (local)

Requires Ollama to be running locally. Pull a model first:

```bash
ollama pull llama3.2
```

## Switching providers

### Via `.env`

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

### Via CLI flags

```bash
# Use Ollama
python src/app.py samples/sample1.docx --provider ollama --model llama3.2

# Use OpenRouter with a specific model
python src/app.py samples/sample1.docx --provider openrouter --model openai/gpt-4o

# Default (reads LLM_PROVIDER from .env)
python src/app.py samples/sample1.docx
```

### Via UI sidebar

Launch the Streamlit app and use the **LLM Provider** panel in the left sidebar to select the provider and model before uploading your document.

```bash
streamlit run src/ui.py
```

---

# 🚀 Running the Project

## CLI Mode

```bash
# Default provider (from .env)
python src/app.py samples/sample1.docx

# Ollama
python src/app.py samples/sample1.docx --provider ollama --model llama3.2

# Debug mode
python src/app.py samples/sample1.docx --debug
```

---

## Interactive UI

```bash
streamlit run src/ui.py
```

---

## Evaluation Suite

```bash
python evaluate.py
```

---

# 📊 Example Output

```json
{
  "heading": "Methodology",
  "type": "methodology",
  "keywords": [
    "chunking",
    "hierarchy",
    "llm"
  ],
  "confidence": 0.89
}
```

---

# ⚠️ Known Limitations

- DOCX only (currently)
- no PDF support yet
- soft heading heuristics can fail
- repeated headings remain challenging
- tables do not yet preserve styling or merged cells

---

# 🚀 Future Work

Planned upgrades:
- PDF support
- advanced table extraction
- entity recognition
- layout-aware parsing
- vector search / RAG
- graph-based document representation
- tree-preserving merge pipeline

---

# 📜 License

Apache License 2.0

---

# 🧠 Key Idea

This project intentionally avoids letting the LLM do everything.

Instead:
- rules reconstruct structure
- LLMs enrich semantics
- scoring estimates reliability

The goal is reliable document understanding, not just text extraction.
