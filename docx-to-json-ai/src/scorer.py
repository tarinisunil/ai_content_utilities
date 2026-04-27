import logging

logger = logging.getLogger(__name__)


def section_text_length(section):
    total = 0

    for item in section.get("content", []):
        if isinstance(item, dict):
            total += len(item.get("text", ""))
        else:
            total += len(str(item))

    return total


def compute_confidence(sections, original_text):
    if not original_text:
        logger.warning("compute_confidence: empty original_text")
        return 0.0

    original_len = len(original_text)

    extracted_len = sum(section_text_length(s) for s in sections)

    coverage = extracted_len / original_len

    logger.info(
        "compute_confidence: extracted=%d, original=%d, coverage=%.2f",
        extracted_len,
        original_len,
        coverage,
    )

    # --- Coverage-based scoring ---
    if coverage >= 0.85:
        base_score = 0.9
    elif coverage >= 0.65:
        base_score = 0.75
    elif coverage >= 0.4:
        base_score = 0.6
    else:
        base_score = 0.4

    # --- Structural bonus ---
    section_count = len(sections)
    avg_section_size = extracted_len / max(section_count, 1)

    if section_count > 3 and avg_section_size > 100:
        base_score += 0.05  # small bonus

    return round(min(base_score, 1.0), 2)