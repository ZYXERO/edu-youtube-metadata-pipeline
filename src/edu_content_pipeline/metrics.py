from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_published_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def add_derived_metrics(row: dict[str, Any]) -> dict[str, Any]:
    """Compute engagement proxies from collected Data API fields."""
    views = row.get("view_count")
    likes = row.get("like_count")
    comments = row.get("comment_count")
    duration_sec = row.get("duration_seconds")

    views_f = float(views) if views is not None and views > 0 else None
    likes_f = float(likes) if likes is not None else 0.0
    comments_f = float(comments) if comments is not None else 0.0

    row["duration_minutes"] = (
        round(duration_sec / 60.0, 2) if duration_sec is not None else None
    )

    if views_f:
        row["like_rate"] = round(likes_f / views_f, 6)
        row["engagement_rate"] = round((likes_f + comments_f) / views_f, 6)
        row["comments_per_1k_views"] = round(1000.0 * comments_f / views_f, 4)
    else:
        row["like_rate"] = None
        row["engagement_rate"] = None
        row["comments_per_1k_views"] = None

    if comments_f > 0:
        row["like_to_comment_ratio"] = round(likes_f / comments_f, 4)
    else:
        row["like_to_comment_ratio"] = None

    published = _parse_published_at(row.get("published_at"))
    if published and views is not None:
        now = datetime.now(timezone.utc)
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        days = max((now - published).total_seconds() / 86400.0, 1.0)
        row["views_per_day"] = round(float(views) / days, 2)
    else:
        row["views_per_day"] = None

    return row
