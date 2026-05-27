from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


_DURATION_RE = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)

CSV_COLUMNS = [
    "video_id",
    "url",
    "title",
    "description",
    "channel_id",
    "channel_title",
    "published_at",
    "duration_seconds",
    "duration_minutes",
    "view_count",
    "like_count",
    "comment_count",
    "like_rate",
    "engagement_rate",
    "comments_per_1k_views",
    "like_to_comment_ratio",
    "views_per_day",
    "tags",
    "category_id",
    "default_language",
    "caption_available",
    "definition",
    "search_query",
    "collection_timestamp_utc",
    "relevance_score",
]

SENTIMENT_COLUMNS = [
    "sentiment_title_label",
    "sentiment_title_score",
    "sentiment_description_label",
    "sentiment_description_score",
    "sentiment_combined_score",
    "sentiment_model",
]


def parse_iso8601_duration(duration: str | None) -> int | None:
    if not duration:
        return None
    match = _DURATION_RE.match(duration)
    if not match:
        return None
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds


def row_from_search(item: dict[str, Any], search_query: str, collected_at: str) -> dict[str, Any]:
    snippet = item.get("snippet", {})
    video_id = item.get("id", {}).get("videoId", "")
    tags = snippet.get("tags") or []
    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "channel_id": snippet.get("channelId", ""),
        "channel_title": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt", ""),
        "duration_seconds": None,
        "view_count": None,
        "like_count": None,
        "comment_count": None,
        "tags": ";".join(tags),
        "category_id": snippet.get("categoryId", ""),
        "default_language": snippet.get("defaultLanguage") or snippet.get("defaultAudioLanguage", ""),
        "caption_available": None,
        "definition": None,
        "search_query": search_query,
        "collection_timestamp_utc": collected_at,
        "relevance_score": None,
    }


def merge_video_details(row: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})

    tags = snippet.get("tags") or []
    if tags:
        row["tags"] = ";".join(tags)
    if snippet.get("categoryId"):
        row["category_id"] = snippet.get("categoryId", row.get("category_id", ""))

    row["duration_seconds"] = parse_iso8601_duration(content.get("duration"))
    row["view_count"] = _int_or_none(stats.get("viewCount"))
    row["like_count"] = _int_or_none(stats.get("likeCount"))
    row["comment_count"] = _int_or_none(stats.get("commentCount"))
    row["caption_available"] = content.get("caption") == "true"
    row["definition"] = content.get("definition", "")
    if snippet.get("defaultLanguage") or snippet.get("defaultAudioLanguage"):
        row["default_language"] = snippet.get("defaultLanguage") or snippet.get(
            "defaultAudioLanguage", ""
        )
    return row


def _int_or_none(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def truncate_description(row: dict[str, Any], max_chars: int) -> dict[str, Any]:
    desc = row.get("description") or ""
    if len(desc) > max_chars:
        row["description"] = desc[: max_chars - 3] + "..."
    return row


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
