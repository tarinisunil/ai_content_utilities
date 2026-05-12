# Naive vs Hierarchical Chunking Demo

## Streamlit UI

Run:

```bash
streamlit run ui.py
```

The UI shows:
- raw naive chunking from extracted blocks
- hierarchical chunking from reconstructed sections
- chunk stats and previews
- section explorer and confidence views
- an LLM provider toggle for OpenRouter or Ollama

## CLI

Run with OpenRouter:

```bash
python app.py path/to/file.docx --provider openrouter
```

Run with Ollama:

```bash
python app.py path/to/file.docx --provider ollama
```

You can also set the default provider with:

```bash
export LLM_PROVIDER=openrouter
```

or:

```bash
export LLM_PROVIDER=ollama
```
