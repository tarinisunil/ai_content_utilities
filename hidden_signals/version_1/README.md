# What Your Documents Whisper When Nobody's Looking

A tiny interactive tool that demonstrates an important idea in knowledge discovery:

> Important is not always what appears most often.
>
> Sometimes important is what connects to many other things.

This tool was created as a companion to the blog post:

**What Your Documents Whisper When Nobody's Looking**

It intentionally avoids:

- AI
- Ollama
- Embeddings
- Vector Databases
- Knowledge Graph Frameworks

Instead, it focuses on a single concept:

**Connections.**

---

## Why This Exists

Most document analysis starts with counting.

Questions like:

- What words appear most often?
- What topics are mentioned the most?
- What terms have the highest frequency?

Frequency is useful.

But frequency is not the only signal.

Sometimes the most interesting idea is the one that connects multiple topics together.

Think about a company.

The most important employee is not always the one who talks the most.

Sometimes it's the person who connects different teams.

Documents behave the same way.

This toy tool helps visualize that idea.

---

## How It Works

Paste one phrase per line.

Example:

```text
RAG and Search
Agents and Memory
Agents and MCP
Memory and MCP
```

Click **Analyze Connections**.

The tool identifies:

- Shared words
- Repeated concepts
- Connection pairs
- Hub concepts

Example output:

```text
Agents ↔ Memory
Agents ↔ MCP
Memory ↔ MCP
```

You begin to see which concepts act as bridges.

---

## The Aha Moment

Most people start by looking for:

> Which word appears most often?

After a few experiments they begin asking:

> Which idea connects to the most other ideas?

That shift is the entire point of the tool.

The goal is not counting.

The goal is seeing structure.

---

## Experiments To Try

### Experiment 1: Create a Hub

```text
Agents and Memory
Agents and Tools
Agents and Planning
Agents and MCP
Agents and Retrieval
```

Expected observation:

- "Agents" becomes a hub.
- Everything points back to a single concept.

### Experiment 2: Create a Chain

```text
Search and Retrieval
Retrieval and Ranking
Ranking and Evaluation
Evaluation and Feedback
```

Expected observation:

- Concepts form a sequence.
- Relationships become more important than individual words.

### Experiment 3: Compare Frequency vs Connections

```text
Search
Search
Search
Search
Search
```

Compare with:

```text
Agents and Search
Agents and Memory
Agents and MCP
Memory and MCP
```

Expected observation:

The first dataset has more repetition.

The second dataset has more structure.

Structure is often more interesting.

---

## What This Tool Does Not Do

This tool only looks at exact words.

It does not understand meaning.

For example:

```text
Search
```

and

```text
Information Retrieval
```

are treated as completely different concepts.

The tool has no semantic understanding.

It only sees text.

---

## Running the Tool

Open:

```text
document_connections_toy_tool.html
```

in any modern browser.

No server required.
