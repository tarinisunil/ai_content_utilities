# Knowledge Radar — Hidden Signals final experiment

A single-file, runnable browser demo for the **Hidden Signals** blog series.

The goal is not to build a generic semantic-search toy. The goal is to let a reader **see the six hidden signals from the series, correlate them with visible evidence, and then try the same experiment on their own sentences**.

The six signals exposed by the demo are:

1. **Connections** — What connects to what?
2. **Meaning** — What is related even when words differ?
3. **Communities** — What ideas gather together?
4. **Movement** — What is changing?
5. **Outliers** — What does not fit yet?
6. **Emergence** — What weak signal is beginning to form a new conversation?

This mirrors the progression of the series: connections, meaning, communities, movement, the documents that do not fit, and finally the Knowledge Radar's “what might be beginning?” perspective. The series itself describes the final combined lens as connections → meaning → communities → movement → outliers, then asks what is happening across the collection and what tiny signal might become important next. See the supplied source material for the original framing.

---

## 1. Quick start

### Requirements

Python 3.10+ is recommended.

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements_plain.txt
```

Run:

```bash
python knowledge_radar_plain.py
```

The browser should open automatically at:

```text
http://127.0.0.1:8765
```

If the browser does not open, paste that URL into your browser.

Press `Ctrl+C` in the terminal to stop the app.

---

## 2. Why this is a browser app instead of a notebook

The final blog post is supposed to feel like an experiment the reader can **touch**.

A notebook is good for explaining the code. It is not as good for creating the moment where a reader thinks:

> “Wait — I changed all the words, but the system still found the same idea.”

or:

> “That document was an outlier in January, but now it has a whole neighborhood.”

The Python script therefore contains:

```text
Python process
    |
    +-- embedding / similarity engine
    +-- clustering
    +-- connection analysis
    +-- temporal analysis
    +-- outlier analysis
    +-- emergence analysis
    |
    +-- tiny HTTP server
             |
             +-- browser UI
```

There is no React project, build step, database server, or notebook dependency.

---

# 3. The six signals

## Signal 1 — Connections

### Question

**What connects to what?**

The first hidden idea in the series is that importance is not always the same thing as frequency. A document can be interesting because it is strongly connected to many other ideas.

### What the demo computes

For every document:

- semantic similarity to every other document
- number of neighbors above a similarity threshold
- average strength of its strongest neighbors

This produces a simple structural view:

```text
Document A
   | \
   |  \
Document B  Document C
       |
       |
    Document D
```

### What the user sees

The **Connections** tab ranks documents by number of strong semantic links.

Clicking a document opens its nearest neighbors and shows:

```text
connections: 8
average neighbor strength: 0.74
```

The important design principle is that the UI shows the evidence rather than saying:

> “This is important.”

It says:

> “This document has many strong connections.”

The reader makes the interpretation.

---

## Signal 2 — Meaning

### Question

**What is related even when words differ?**

This is the semantic-embedding experiment from the series.

Example:

```text
Agents need memory to maintain context.
```

versus:

```text
How can an autonomous system remember what happened earlier?
```

A keyword search may miss the relationship.

An embedding model can place the ideas near one another.

### What the demo computes

The preferred backend is:

```text
sentence-transformers
all-MiniLM-L6-v2
```

The sentence becomes an embedding vector, and cosine similarity is used to find nearby documents.

### The WOW interaction

The demo opens with:

```text
How can an autonomous system remember what happened earlier?
```

The user clicks:

**Find hidden neighbors**

Then the instruction is to rewrite the idea using completely different vocabulary.

That is the moment to highlight in the blog.

The point is not that the model “understands” the user in a human sense. The point is that the semantic representation makes a relationship visible even after the vocabulary changes.

---

## Signal 3 — Communities

### Question

**What ideas gather together?**

Individual similarities become more interesting when many documents gather around the same region.

### What the demo computes

The embeddings are clustered with DBSCAN.

The reader sees:

```text
Community 0   15 documents
Community 1   11 documents
Community 2    8 documents
Edge / unassigned  4 documents
```

Clicking a community shows representative documents.

The key idea is:

```text
single document -> relationship
cluster         -> conversation
```

That is the conceptual jump made in the series.

---

## Signal 4 — Movement

### Question

**What is changing?**

A single snapshot tells us what exists now.

A sequence of snapshots lets us observe change.

### What the demo computes

Documents retain their `month` field:

```text
January
February
March
April
```

For each month, the demo calculates community membership and compares the structure between successive months.

The interface highlights:

- growth
- shrinking activity
- potential specialization / splitting
- structural changes

### Why the time slider matters

The reader drags:

```text
January ---- February ---- March ---- April
```

and watches the dataset change.

This turns the idea of “movement” into something visual rather than explanatory prose.

---

## Signal 5 — Outliers

### Question

**What does not fit yet?**

The important qualification is:

> outlier does not mean important

An outlier may be:

- noise
- a one-off note
- a mistake
- an unusual request
- the beginning of a new topic

### What the demo computes

For each document, an outlier score is derived from the strength of its closest neighbors.

A document whose nearest neighbors are weak receives a higher outlier score.

The UI explicitly labels this as:

> **Outlier: weak local neighborhood**

not:

> **Future trend**

That distinction keeps the demo honest.

---

## Signal 6 — Emergence

### Question

**What weak signal is beginning to form a new conversation?**

This is the last layer of the Knowledge Radar.

The demo looks for a very specific pattern:

```text
EARLY
one strange / weakly connected idea

        ↓

LATER
related ideas begin appearing

        ↓

NOW
small semantic neighborhood
```

### The built-in example

January starts with:

```text
We need to trace every action an autonomous agent performs.
```

It is relatively lonely.

Later, documents appear such as:

```text
How can we inspect an agent's tool calls?
We need logs for autonomous agent actions.
Agent traces should show every tool invocation.
Debugging agents requires visibility into their decisions.
```

The original document becomes interesting because its semantic neighborhood grows.

### Important wording

The interface deliberately calls this:

> **Emergence evidence**

not:

> **Prediction**

The system is not claiming that a future event is guaranteed.

The evidence is:

```text
1 early unusual idea
+
multiple later semantically related documents
=
possible emerging conversation
```

That is the signal the reader can inspect for themselves.

---

# 4. The final Knowledge Radar

The six signals are separate views because each answers a different question.

The combined mental model is:

```text
CONNECTIONS
    |
    v
What is structurally linked?

MEANING
    |
    v
What is related despite different language?

COMMUNITIES
    |
    v
What conversations exist?

MOVEMENT
    |
    v
What conversations are changing?

OUTLIERS
    |
    v
What does not fit yet?

EMERGENCE
    |
    v
What weak signal is beginning to form?
```

The final article can then show the Knowledge Radar as the combination of these lenses rather than as a mysterious score.

---

# 5. Stage 1 — Make the signal engine work

Do this before worrying about aesthetics.

## Step 1: Embed the documents

Use:

```python
SentenceTransformer("all-MiniLM-L6-v2")
```

and encode the text.

If sentence-transformers cannot be loaded, the demo falls back to TF-IDF so the program still runs. The full “meaning rather than keyword overlap” experiment requires the embedding backend.

## Step 2: Similarity matrix

Compute:

```text
cosine_similarity(embedding_i, embedding_j)
```

This gives the relationship graph.

## Step 3: Connections

Count strong semantic neighbors for every document.

This produces the connection signal.

## Step 4: Communities

Run DBSCAN over the embedding vectors.

This gives community membership without hand-written topic labels.

## Step 5: Outliers

Look at the strength of each document's strongest local neighbors.

Weak neighborhood => high outlier score.

## Step 6: Movement

Do the same analysis within each month.

Compare month-to-month structure.

## Step 7: Emergence

For an earlier document, count later documents that become semantically similar.

An earlier outlier + later neighborhood is the main emergence pattern.

---

# 6. Stage 2 — Make the signals explainable

This is where the demo becomes useful for a blog reader.

Never show only a single mysterious score.

For a selected document, the demo exposes:

```text
Document

Month

Connection count
Average neighbor similarity
Community
Outlier score
Nearest semantic neighbors
Emergence evidence
```

The reader can therefore correlate a signal with its evidence.

For example:

```text
SIGNAL: OUTLIER

Outlier score: 0.83
Connection count: 1

January
"We need to trace every action an autonomous agent performs."

Later related documents: 5
```

The interpretation is left to the reader.

---

# 7. Stage 3 — Make it a WOW demo

The recommended reader journey is:

## WOW 1 — Rephrase

Start with:

```text
How can an autonomous system remember what happened earlier?
```

Then change it to something like:

```text
How does software preserve context across a long-running task?
```

The same conceptual neighborhood should remain visible when semantic embeddings are available.

## WOW 2 — Click a cluster

Move to **Communities** and show that documents naturally group together.

## WOW 3 — Move time

Move January -> April.

Show a growing and changing conversation.

## WOW 4 — Find the lonely document

Select the January observability document.

Then inspect its later neighbors.

## WOW 5 — Bring your own sentences

Paste:

```text
January | Customer complaints mention slow search.
February | Search results are difficult to navigate.
March | Users want better topic summaries.
April | Customers ask whether the system can surface emerging themes.
```

Run the radar again.

Now the reader has moved from “demo data” to their own ideas.

That is the point at which the experiment becomes memorable.

---

# 8. Suggested final blog structure

## Opening

**We said we'd build it. So let's build it.**

Keep the recap short.

## Section 1 — Open the demo

Show the six signals as the navigation.

## Section 2 — Signal 1: Connections

Explain one document that has many relationships.

## Section 3 — Signal 2: Meaning

Do the rephrasing experiment.

## Section 4 — Signal 3: Communities

Show the clusters.

## Section 5 — Signal 4: Movement

Drag the month slider.

## Section 6 — Signal 5: Outliers

Find the lonely document.

## Section 7 — Signal 6: Emergence

Follow that document forward in time.

## Section 8 — Bring your own data

Paste a mini dataset.

## Section 9 — Build the Knowledge Radar

Put the six views together.

## Section 10 — What this does not prove

Make the limitations explicit.

A good ending is not:

> “The AI predicted the future.”

A better ending is:

> “The data already contained the signal. We just changed how we looked at it.”

---

# 9. Implementation notes

## Why no vector database?

For the demo, you do not need one.

The dataset is intentionally small enough to keep embeddings in memory.

That makes the experiment easier for readers to reproduce.

For production-scale use, replace the in-memory matrix with something like Qdrant, pgvector, or another vector store.

## Why PCA?

The browser needs a 2D map.

PCA compresses the embedding vectors into two coordinates for visualization.

The 2D map is a visualization, not the actual semantic space.

The similarity calculations still use the original embedding representation.

## Why DBSCAN?

DBSCAN is convenient for a demo because it can leave documents unassigned as noise instead of forcing every document into a predefined number of clusters.

This fits the series' outlier story.

---

# 10. Limitations and honest interpretation

This demo is intentionally a signal detector, not a truth engine.

### Similarity is not understanding

A high cosine similarity says the embedding representations are close. It does not prove that two documents are logically equivalent.

### Cluster labels are not ground truth

The communities emerge from the chosen representation and clustering parameters.

### Outlier is not “important”

It means “unusual relative to this collection.”

### Emergence is not guaranteed prediction

The demo identifies an earlier weak signal whose semantic neighborhood grows later. That is evidence of emergence, not a guarantee about the future.

### Small datasets can be unstable

Changing the corpus, embedding model, or threshold can change the shape of the map.

These caveats belong in the final post because they make the experiment more credible rather than less interesting.

---

# 11. File layout

```text
knowledge_radar_demo/
├── knowledge_radar_plain.py
├── requirements_plain.txt
├── README.md
└── IMPLEMENTATION_PLAN.md
```

The main application is deliberately one Python file.

---

# 12. Suggested next step after the blog

Once the blog/demo combination works, the natural production evolution is:

```text
small local demo
      ↓
CSV / JSON ingestion
      ↓
real document chunks
      ↓
vector database
      ↓
periodic snapshots
      ↓
community tracking
      ↓
Knowledge Radar dashboard
```

That is where the experiment stops being a teaching toy and becomes a reusable knowledge-observation system.
