from __future__ import annotations

from typing import Any


def dedupe_rows(rows: list[dict[str, Any]], key: str = "video_id") -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        vid = row.get(key)
        if not vid or vid in seen:
            continue
        seen.add(vid)
        unique.append(row)
    return unique
