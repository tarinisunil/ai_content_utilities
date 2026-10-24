# Knowledge Radar — quick plain-text README

Run:

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements_plain.txt
    python knowledge_radar_plain.py

Open:

    http://127.0.0.1:8765

The demo exposes six signals:

1. Connections — What connects to what?
2. Meaning — What is related even when words differ?
3. Communities — What ideas gather together?
4. Movement — What is changing?
5. Outliers — What does not fit yet?
6. Emergence — What weak signal is beginning to form a new conversation?

WOW path:

1. Rewrite the sentence in the playground using completely different words.
2. Compare semantic neighbors.
3. Open Communities.
4. Move January -> April.
5. Find the lonely observability document.
6. Inspect its later neighbors.
7. Paste your own mini knowledge base.

The full README and implementation plan explain the algorithms, evidence model, limitations and recommended blog structure.
