import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _iter_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Return a flat list of all sections, including nested children.
    Works for both flat outputs and tree-shaped outputs.
    """
    flat: List[Dict[str, Any]] = []

    def walk(items: List[Dict[str, Any]]) -> None:
        for sec in items:
            if not isinstance(sec, dict):
                continue
            flat.append(sec)
            children = sec.get("children", [])
            if isinstance(children, list) and children:
                walk(children)

    walk(sections or [])
    return flat


def section_text_length(section: Dict[str, Any]) -> int:
    """
    Count characters in a section's content.
    """
    total = 0

    for item in section.get("content", []):
        if isinstance(item, dict):
            total += len(item.get("text", "") or "")
        else:
            total += len(str(item))

    return total


def total_text_length(sections: List[Dict[str, Any]]) -> int:
    """
    Sum text length across all sections, including nested children.
    """
    return sum(section_text_length(sec) for sec in _iter_sections(sections))


def count_sections(sections: List[Dict[str, Any]]) -> int:
    return len(_iter_sections(sections))


def max_depth(sections: List[Dict[str, Any]]) -> int:
    """
    Compute the deepest nesting level in the section tree.
    """
    if not sections:
        return 0

    deepest = 0

    def walk(items: List[Dict[str, Any]], current_depth: int) -> None:
        nonlocal deepest
        for sec in items:
            if not isinstance(sec, dict):
                continue
            deepest = max(deepest, current_depth)
            children = sec.get("children", [])
            if isinstance(children, list) and children:
                walk(children, current_depth + 1)

    walk(sections, 1)
    return deepest


def average_section_confidence(sections: List[Dict[str, Any]]) -> float:
    """
    Average confidence across all sections that have a numeric confidence.
    """
    values = []

    for sec in _iter_sections(sections):
        conf = sec.get("confidence")
        if isinstance(conf, (int, float)):
            values.append(float(conf))

    if not values:
        return 0.0

    return sum(values) / len(values)


def keyword_quality_score(sections: List[Dict[str, Any]]) -> float:
    """
    Score keyword extraction quality based on:
    - whether sections have keywords at all
    - whether keyword lists are reasonably sized
    """
    secs = _iter_sections(sections)
    if not secs:
        return 0.0

    filled = 0
    good = 0

    for sec in secs:
        kws = sec.get("keywords", [])
        if isinstance(kws, list) and kws:
            filled += 1
            if 3 <= len(kws) <= 7:
                good += 1

    coverage = filled / len(secs)
    shape_quality = good / len(secs)

    return round((0.6 * coverage) + (0.4 * shape_quality), 3)


def structure_quality_score(sections: List[Dict[str, Any]]) -> float:
    """
    Reward documents that have multiple sections and some hierarchy.
    Penalize documents that are too flat or too sparse.
    """
    secs = _iter_sections(sections)
    section_count = len(secs)

    if section_count == 0:
        return 0.0

    depth = max_depth(sections)
    top_level_count = len(sections)

    # Basic section count quality
    if section_count >= 8:
        count_score = 1.0
    elif section_count >= 5:
        count_score = 0.85
    elif section_count >= 3:
        count_score = 0.7
    else:
        count_score = 0.4

    # Depth quality
    if depth >= 3:
        depth_score = 1.0
    elif depth == 2:
        depth_score = 0.8
    elif depth == 1:
        depth_score = 0.55
    else:
        depth_score = 0.0

    # If there is only one top-level section, the doc is probably too flat
    if top_level_count <= 1 and section_count > 1:
        flat_penalty = 0.15
    else:
        flat_penalty = 0.0

    score = (0.55 * count_score) + (0.45 * depth_score) - flat_penalty
    return round(max(0.0, min(score, 1.0)), 3)


def coverage_score(sections: List[Dict[str, Any]], original_text: str) -> float:
    """
    Measure how much of the source text is represented in the extracted sections.
    """
    if not original_text:
        logger.warning("coverage_score: empty original_text")
        return 0.0

    original_len = len(original_text)
    extracted_len = total_text_length(sections)

    if original_len <= 0:
        return 0.0

    coverage = extracted_len / original_len

    # Convert raw coverage into a score band.
    if coverage >= 0.90:
        return 1.0
    elif coverage >= 0.75:
        return 0.85
    elif coverage >= 0.55:
        return 0.70
    elif coverage >= 0.35:
        return 0.50
    else:
        return 0.25


def compute_confidence(sections: List[Dict[str, Any]], original_text: str) -> float:
    """
    Compute a document-level confidence score from multiple signals.

    Signals:
    - coverage: how much source text was captured
    - section confidence: average confidence across sections
    - keyword quality: whether the section annotations look healthy
    - structure quality: whether the doc has sensible nesting and section count
    """
    if not sections:
        logger.warning("compute_confidence: empty sections")
        return 0.0

    cov = coverage_score(sections, original_text)
    avg_sec_conf = average_section_confidence(sections)
    kw_score = keyword_quality_score(sections)
    struct_score = structure_quality_score(sections)

    # Weighted blend
    final = (
        0.40 * cov +
        0.30 * avg_sec_conf +
        0.15 * kw_score +
        0.15 * struct_score
    )

    # Small bonus if the document looks healthy overall
    if cov >= 0.75 and avg_sec_conf >= 0.70 and struct_score >= 0.70:
        final += 0.03

    final = round(min(max(final, 0.0), 1.0), 2)

    logger.info(
        "compute_confidence: coverage=%.2f avg_section=%.2f keywords=%.2f structure=%.2f final=%.2f",
        cov,
        avg_sec_conf,
        kw_score,
        struct_score,
        final,
    )

    return final
