# Knowledge Radar — Implementation Plan

## Goal

Build a reproducible interactive experiment that lets a reader observe all six hidden signals from the Hidden Signals series rather than merely reading about them.

## Canonical six-signal model

| # | Signal | Reader question | Demo evidence |
|---|---|---|---|
| 1 | Connections | What connects to what? | neighbor count + average neighbor strength |
| 2 | Meaning | What is related despite different words? | query embedding + nearest neighbors |
| 3 | Communities | What ideas gather together? | DBSCAN communities |
| 4 | Movement | What is changing? | month-by-month community sizes/events |
| 5 | Outliers | What does not fit yet? | weak local neighborhood / outlier score |
| 6 | Emergence | What weak signal is beginning? | early outlier + later semantic neighborhood |

## Stage 1 — Signal engine

### Input

Small synthetic corpus with:

- stable AI evaluation documents
- growing agent documents
- document processing documents
- an early agent-observability outlier
- later observability documents
- months January-April

### Processing

1. Encode all documents.
2. Build cosine-similarity matrix.
3. Count semantic connections.
4. Cluster embeddings.
5. Calculate outlier score.
6. Compare month-to-month community structure.
7. Count later neighbors for earlier documents.
8. Project embeddings to 2D for visualization.

### Outputs

```text
embeddings
similarity matrix
cluster labels
connection counts
outlier scores
movement events
emergence scores
2D coordinates
```

## Stage 2 — Evidence-first interface

The UI should never hide everything behind a single “AI insight.”

For every signal, show:

- the question being answered
- the calculation that supports it
- concrete documents
- a visible score where useful
- a short interpretation
- a warning where interpretation could be misleading

### Example

Instead of:

```text
Agent Observability is the next trend.
```

show:

```text
Emergence evidence

January: one weakly connected document
February: 2 later related documents
March: 5 later related documents
April: 7+ related documents
```

Let the reader make the connection.

## Stage 3 — WOW interaction design

### Interaction A: Rewrite

Reader types a sentence.

They are explicitly encouraged to rewrite it with different vocabulary.

The result shows nearest semantic neighbors.

### Interaction B: Map

Reader clicks documents and communities.

### Interaction C: Time

Reader drags the month slider.

### Interaction D: Outlier

Reader finds a lonely document.

### Interaction E: Trace forward

Reader inspects whether similar documents appear later.

### Interaction F: Bring your own data

Reader pastes one sentence per line or `Month | sentence`.

The same pipeline runs immediately.

## Data story embedded in the demo

The built-in example should intentionally produce this narrative:

```text
January
  AI agents
  Evaluation
  Document processing
  + one lonely observability idea

February
  Agent topics grow
  A few observability neighbors appear

March
  Observability becomes a small neighborhood
  Agent topics become more specialized

April
  Memory / Planning / Security separate
  Observability becomes recognizable
  Document processing + extraction move closer
```

The purpose is not to fake a prediction. It is to make the same causal-looking sequence visible enough that a reader can inspect the underlying documents.

## Code architecture

```text
knowledge_radar_plain.py
│
├── DEMO_ROWS
├── SIGNALS
├── RadarEngine
│   ├── embedding backend
│   ├── similarity
│   ├── connection metrics
│   ├── clustering
│   ├── outliers
│   ├── movement
│   └── emergence
│
├── HTTP API
│   ├── GET /api/data
│   ├── GET /api/query?q=...
│   └── POST /api/custom
│
└── single-page browser UI
```

## API contract

### GET `/api/data`

Returns the current dataset plus all computed signals.

### GET `/api/query?q=...`

Embeds the user query and returns nearest semantic neighbors.

### POST `/api/custom`

Accepts:

```json
[
  {"id":"U001","month":"January","text":"..."},
  {"id":"U002","month":"February","text":"..."}
]
```

The engine is rebuilt immediately.

## Validation checklist

Before publishing the final post, test these exact reader journeys:

### Connections

- click a high-connection document
- inspect its neighbors
- explain why it is structurally central

### Meaning

- enter a paraphrase that shares very few keywords
- verify semantically related documents still appear with the embedding backend

### Communities

- confirm multiple clusters appear
- inspect documents in each cluster

### Movement

- move January -> April
- observe changing community sizes
- inspect structural events

### Outliers

- identify the January observability document
- confirm it has a high outlier score

### Emergence

- confirm the same earlier document has later related neighbors
- show that the neighborhood grows

### User data

- paste 6-20 lines
- use months
- query one idea with new wording
- verify the application rebuilds without restarting

## Publishing checklist

1. Host or run the Python demo.
2. Put the demo link near the top of the final blog post.
3. Show a 20-40 second screen recording of the rephrase experiment.
4. Show the January-to-April time slider.
5. Show the outlier becoming an emerging neighborhood.
6. Include the GitHub repository.
7. Include the dataset.
8. Include limitations.

## What to say in the final article

The safest and strongest framing is:

> The radar does not tell us what will happen. It lets us see relationships, structure, change and weak signals that are difficult to notice when we read documents one at a time.

That keeps the experiment aligned with the series and avoids turning an exploratory signal into an unsupported forecast.
