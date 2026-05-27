from __future__ import annotations

import re
from typing import Any


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def relevance_score(row: dict[str, Any], keywords: list[str]) -> float:
    """Keyword overlap score in [0, 1] based on title + description."""
    if not keywords:
        return 1.0
    text = f"{row.get('title', '')} {row.get('description', '')}"
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    keyword_set = set(keywords)
    hits = tokens & keyword_set
    return round(len(hits) / len(keyword_set), 4)


def apply_relevance_filter(
    rows: list[dict[str, Any]],
    keywords: list[str],
    min_score: float,
) -> list[dict[str, Any]]:
    if min_score <= 0:
        for row in rows:
            row["relevance_score"] = relevance_score(row, keywords)
        return rows

    kept: list[dict[str, Any]] = []
    for row in rows:
        score = relevance_score(row, keywords)
        row["relevance_score"] = score
        if score >= min_score:
            kept.append(row)
    return kept
