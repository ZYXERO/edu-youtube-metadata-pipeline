from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from edu_content_pipeline.config import AppConfig
from edu_content_pipeline.dedupe import dedupe_rows
from edu_content_pipeline.export_csv import export_csv
from edu_content_pipeline.filter import apply_relevance_filter
from edu_content_pipeline.manifest import RunManifest, utc_now_iso
from edu_content_pipeline.metrics import add_derived_metrics
from edu_content_pipeline.normalize import (
    merge_video_details,
    row_from_search,
    truncate_description,
    utc_now_iso as collect_ts,
)
from edu_content_pipeline.youtube_client import YouTubeClient, sleep_ms

logger = logging.getLogger(__name__)


def _collect_query(
    client: YouTubeClient,
    config: AppConfig,
    query: str,
    collected_at: str,
    target: int,
) -> list[dict[str, Any]]:
    """Fetch up to `target` videos for a single search query."""
    query_rows: list[dict[str, Any]] = []
    page_token: str | None = None
    max_pages = config.collection.max_pages_per_query

    for page_num in range(max_pages):
        if len(query_rows) >= target:
            break

        logger.info(
            "Searching query=%r page=%s (%s/%s videos)",
            query,
            page_num + 1,
            len(query_rows),
            target,
        )
        response = client.search_videos(
            query,
            max_results=50,
            page_token=page_token,
            order=config.collection.order,
            relevance_language=config.collection.relevance_language,
            safe_search=config.collection.safe_search,
            video_category_id=config.collection.video_category_id,
        )

        for item in response.get("items", []):
            if len(query_rows) >= target:
                break
            if item.get("id", {}).get("kind") != "youtube#video":
                continue
            query_rows.append(row_from_search(item, query, collected_at))

        page_token = response.get("nextPageToken")
        sleep_ms(config.collection.sleep_ms_between_search)
        if not page_token:
            break

    return query_rows


def collect(config: AppConfig, client: YouTubeClient) -> RunManifest:
    target = config.collection.results_per_query
    manifest = RunManifest(
        started_at_utc=utc_now_iso(),
        config_path=str(config.config_path),
        queries=config.queries,
        results_per_query=target,
        expected_raw_rows=len(config.queries) * target,
    )

    collected_at = collect_ts()
    raw_rows: list[dict[str, Any]] = []
    per_query_counts: dict[str, int] = {}

    for query in config.queries:
        try:
            query_rows = _collect_query(client, config, query, collected_at, target)
        except Exception as exc:
            logger.error("Search failed for %r: %s", query, exc)
            manifest.notes.append(f"search_error:{query}:{exc}")
            query_rows = []

        per_query_counts[query] = len(query_rows)
        raw_rows.extend(query_rows)

        if len(query_rows) < target:
            manifest.notes.append(
                f"query_short:{query}: got {len(query_rows)}, wanted {target}"
            )

    manifest.per_query_counts = per_query_counts
    manifest.raw_rows_before_dedupe = len(raw_rows)
    rows = dedupe_rows(raw_rows)
    manifest.unique_video_ids = len(rows)

    video_ids = [r["video_id"] for r in rows if r.get("video_id")]
    details_by_id: dict[str, dict[str, Any]] = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        logger.info("Fetching video details %s-%s of %s", i + 1, i + len(chunk), len(video_ids))
        items = client.get_video_details(chunk)
        for item in items:
            details_by_id[item["id"]] = item
        sleep_ms(config.collection.sleep_ms_between_search)

    for row in rows:
        detail = details_by_id.get(row["video_id"])
        if detail:
            merge_video_details(row, detail)
        add_derived_metrics(row)

    rows = apply_relevance_filter(
        rows,
        config.filter.educational_keywords,
        config.filter.min_relevance_score,
    )
    manifest.rows_after_filter = len(rows)

    for row in rows:
        truncate_description(row, config.export.description_max_chars)

    if len(rows) < config.collection.min_total_rows:
        manifest.status = "failed_min_rows"
        manifest.notes.append(
            f"Only {len(rows)} unique rows; need {config.collection.min_total_rows}"
        )
    else:
        manifest.status = "success"

    export_csv(rows, config.output.csv_path)
    manifest.csv_path = str(config.output.csv_path)

    if config.output.raw_json_dir:
        _write_raw_snapshot(config.output.raw_json_dir, rows, manifest.started_at_utc)

    manifest.quota_units_estimated = client.quota_units_used
    manifest.finished_at_utc = utc_now_iso()
    manifest.write(config.output.manifest_path)
    return manifest


def _write_raw_snapshot(raw_dir: Path, rows: list[dict[str, Any]], started_at: str) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = started_at.replace(":", "").replace("+00:00", "Z")
    path = raw_dir / f"run_{stamp}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    logger.info("Wrote raw snapshot %s", path)
