# DOCX to JSON

Converts a `.docx` into structured JSON using **python-docx** for extraction and an LLM (via OpenRouter) to improve and normalize each chunk.

## Python version

**Python 3.12.8** — tested on macOS.

## How it works

1. **Extract** — Read the document as typed blocks: headings (with level), list/bullet lines, and paragraphs, based on Word styles.
2. **Structure** — Group blocks into sections (a section starts at each heading; text before the first heading is under `"Introduction"`).
3. **Chunk** — Pack sections into chunks (default max ~1500 characters of text per chunk) so the model can process long documents in multiple calls. Very large sections are sent as one chunk, with a warning in the logs.
4. **LLM** — For each chunk, the model returns a JSON **array** of section objects (improved `content` blocks, optional keywords from the model). Each chunk is retried up to 3 times on failure, with a short delay between attempts.
5. **Merge** — Concatenate chunk results into one object: all sections, a **deduplicated** list of `keywords` across chunks, plus title and `notes` when the model returns a document-shaped object.
6. **Confidence** — A document-level `confidence` in the range 0–1 is computed in code from source coverage (and a small structural bonus). This **replaces** any merged confidence from earlier steps; see `src/scorer.py`.

Larger files use **more** LLM requests than a single end-to-end pass, so expect longer runs and more API usage than a one-shot pipeline.

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv venv
```

### 2. Activate it

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. OpenRouter (LLM)

This project uses OpenRouter for inference. In the project root, create a `.env` file:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Run

```bash
python src/app.py path/to/your.docx
```

**Debug mode** (writes prompts and raw parsed outputs, appended, with separators — useful for troubleshooting):

```bash
python src/app.py path/to/your.docx --debug
```

In debug mode, the app creates or appends to `debug_prompt.txt` and `debug_output.txt` in the **current working directory**. Remove or add those files to `.gitignore` if you do not want them in version control.

**Notes**

- `python src/app.py` — Print JSON to **stdout**; use shell redirection to save, e.g. `python src/app.py input/sample.docx > out.json`
- If you also use Conda, deactivate the Conda env before using this project’s venv: `conda deactivate`, then `source venv/bin/activate`
- When done: `deactivate`

## Output (shape)

Printed JSON is a **single object** validated with Pydantic:

- **`title`**
- **`sections`** — each has **`heading`**, **`type`** (e.g. `"general"`), and **`content`**: a list of **content blocks**, each with **`type`** (e.g. `paragraph` / `bullet`) and **`text`**
- **`keywords`** — merged, deduplicated list from model output across chunks
- **`notes`** — combined when present from merged dict-shaped responses
- **`confidence`** — final document score in `[0, 1]` (from the scorer in `app.py`, not the model’s per-section or merge-only averages)

For the exact model, see `src/schema.py`.
