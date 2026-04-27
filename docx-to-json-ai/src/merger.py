import logging

logger = logging.getLogger(__name__)


def merge_results(results):
    final = {
        "title": "",
        "sections": [],
        "keywords": [],
        "confidence": 0.0,
        "notes": []
    }

    all_confidences = []
    keyword_set = set()

    for r in results:
        if isinstance(r, list):
            final["sections"].extend(r)

            for section in r:
                for kw in section.get("keywords", []):
                    if kw not in keyword_set:
                        keyword_set.add(kw)
                        final["keywords"].append(kw)

        elif isinstance(r, dict):
            final["sections"].extend(r.get("sections", []))

            # Keywords
            for kw in r.get("keywords", []):
                if kw not in keyword_set:
                    keyword_set.add(kw)
                    final["keywords"].append(kw)

            # Confidence
            conf = r.get("confidence")
            if isinstance(conf, (int, float)):
                all_confidences.append(conf)

            # Notes
            notes = r.get("notes", [])
            if isinstance(notes, list):
                final["notes"].extend(notes)

            # Title
            if not final["title"] and r.get("title"):
                final["title"] = r["title"]

        else:
            logger.warning("Skipping unexpected result type: %s", type(r))

    # Aggregate confidence
    if all_confidences:
        final["confidence"] = sum(all_confidences) / len(all_confidences)

    logger.info(
        "merge_results: merged %d results into %d sections",
        len(results),
        len(final["sections"])
    )

    return final