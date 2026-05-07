# 📂 Sample Documents

This folder contains evaluation and stress-test documents used by the pipeline.

---

# Included Samples

## `sample1.docx`
Research-style document.

Tests:
- hierarchical headings
- nested sections
- clean structure
- report classification

Expected:
- strong hierarchy reconstruction
- high confidence

---

## `sample2.docx`
Engineering proposal document.

Tests:
- proposal-style writing
- semantic classification
- structured recommendations

Expected:
- proposal/report classification
- medium-to-high confidence

---

## `sample3.docx`
Meeting notes document.

Tests:
- operational content
- repeated topics
- note-style structure

Expected:
- notes classification
- flatter hierarchy

---

## `sample4.docx`
Messy real-world stress test.

Contains:
- missing headings
- inconsistent bullets
- repeated pseudo-headings
- random paragraphs

Tests:
- soft heading heuristics
- failure recovery
- hierarchy reconstruction robustness

Expected:
- lower confidence
- partial hierarchy recovery

---

## `sample5.docx`
Table-heavy document.

Contains:
- multiple headings
- structured evaluation tables
- paragraphs + bullets + tables

Tests:
- table extraction
- row serialization
- table-aware chunking
- mixed content flow

Expected:
- table blocks preserved in JSON
- tables rendered in Streamlit UI
- stable confidence scoring

---

# Evaluation Files

Each sample has a matching:

```text
sampleX.expected.json
```

These files define:
- minimum section count
- minimum hierarchy depth
- required metadata
- allowed document types

---

# Running Evaluation

From project root:

```bash
python evaluate.py
```

This validates:
- hierarchy quality
- metadata generation
- summary generation
- confidence scoring
- document classification