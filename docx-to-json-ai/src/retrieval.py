import re
from typing import Any, Dict, List, Tuple

from chunker import section_to_text

STOPWORDS = {
    "the", "is", "what", "were", "does", "a", "an", "in", "of", "and", "or",
    "to", "it", "this", "that", "are", "was", "be", "for", "on", "with", "at",
    "by", "from", "as", "how", "do", "did", "has", "have", "had", "not", "no",
    "can", "will", "would", "should", "could", "about", "say", "says",
}


def tokenize(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS]


def _naive_chunk_text(chunk: List[Dict[str, Any]]) -> str:
    return " ".join(block.get("text", "") or "" for block in chunk)


def _hierarchical_chunk_text(chunk: List[Dict[str, Any]]) -> str:
    parts = []
    for sec in chunk:
        path = " > ".join(sec.get("path", []) or [])
        heading = sec.get("heading", "") or ""
        body = section_to_text(sec)
        parts.append(f"{path} {heading} {body}")
    return " ".join(parts)


def _score_chunk(terms: List[str], text: str) -> Tuple[int, List[str]]:
    text_terms = set(tokenize(text))
    matched = [t for t in terms if t in text_terms]
    return len(matched), matched


def _get_preview(chunk: List[Dict[str, Any]], mode: str) -> str:
    if mode == "hierarchical":
        lines = []
        for sec in chunk[:2]:
            path = " > ".join(sec.get("path", []) or []) or sec.get("heading", "(untitled)")
            content = sec.get("content", [])
            preview_text = ""
            if content and isinstance(content[0], dict):
                preview_text = (content[0].get("text", "") or "")[:100]
            lines.append(f"[{path}] {preview_text}")
        return "\n".join(lines)
    else:
        return _naive_chunk_text(chunk)[:200]


def _hierarchical_explanation(matched_terms: List[str], chunk: List[Dict[str, Any]]) -> str:
    term_str = ", ".join(f'"{t}"' for t in matched_terms)
    # Find the first section whose heading/path contains a matched term
    matching_sec = None
    for sec in chunk:
        structural_tokens = " ".join(
            p.lower()
            for p in ([sec.get("heading", "")] + (sec.get("path", []) or []))
            if p
        )
        if any(t in structural_tokens for t in matched_terms):
            matching_sec = sec
            break
    if matching_sec is not None:
        path_str = " > ".join(matching_sec.get("path", []) or [])
        label = f"'{path_str}'" if path_str else "section heading"
        return f"Matched section heading/path {label} and body text for: {term_str}."
    return f"Matched body text within a structured section for: {term_str}."


def _naive_explanation(matched_terms: List[str], chunk: List[Dict[str, Any]]) -> str:
    term_str = ", ".join(f'"{t}"' for t in matched_terms)
    types = {b.get("type", "") for b in chunk}
    if len(types) > 2:
        return f"Matched {term_str} but block types are mixed — context may be unrelated."
    return f"Matched {term_str}. Heading not preserved — section context is lost."


def _build_explanation(
    mode: str,
    matched_terms: List[str],
    chunk: List[Dict[str, Any]],
    score: int,
) -> str:
    if score == 0:
        return "No matching terms found."
    if mode == "hierarchical":
        return _hierarchical_explanation(matched_terms, chunk)
    return _naive_explanation(matched_terms, chunk)


def retrieve(
    question: str,
    chunks: List[List[Dict[str, Any]]],
    mode: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Score all chunks by keyword overlap and return the top_k matches.

    Args:
        question: Natural-language question string.
        chunks:   List of chunks — each chunk is List[Dict] (blocks for naive,
                  sections for hierarchical).
        mode:     "naive" or "hierarchical".
        top_k:    Number of top results to return.

    Returns:
        List of result dicts sorted by score descending.
    """
    terms = tokenize(question)
    scored = []

    for i, chunk in enumerate(chunks):
        if mode == "hierarchical":
            text = _hierarchical_chunk_text(chunk)
        else:
            text = _naive_chunk_text(chunk)

        score, matched = _score_chunk(terms, text)
        why = _build_explanation(mode, matched, chunk if mode == "hierarchical" else [], score)
        preview = _get_preview(chunk, mode)

        scored.append({
            "question": question,
            "mode": mode,
            "chunk_idx": i,
            "score": score,
            "matched_terms": matched,
            "preserves_context": mode == "hierarchical",
            "why": why,
            "preview": preview,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    results = []
    for rank, r in enumerate(scored[:top_k], 1):
        r["rank"] = rank
        results.append(r)

    return results
