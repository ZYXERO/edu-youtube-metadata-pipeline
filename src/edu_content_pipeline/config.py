from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class OutputConfig:
    csv_path: Path
    manifest_path: Path
    raw_json_dir: Path | None


@dataclass
class CollectionConfig:
    results_per_query: int
    min_total_rows: int
    sleep_ms_between_search: int
    order: str
    relevance_language: str
    safe_search: str
    video_category_id: str | None

    @property
    def max_pages_per_query(self) -> int:
        """YouTube returns max 50 results per search page."""
        return max(1, (self.results_per_query + 49) // 50)


@dataclass
class FilterConfig:
    min_relevance_score: float
    educational_keywords: list[str]


@dataclass
class ExportConfig:
    description_max_chars: int


@dataclass
class SentimentConfig:
    enabled: bool
    output_csv_path: Path


@dataclass
class AppConfig:
    output: OutputConfig
    collection: CollectionConfig
    queries: list[str]
    filter: FilterConfig
    export: ExportConfig
    sentiment: SentimentConfig
    config_path: Path


def _path(value: str, base: Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else base / p


def load_config(config_path: Path, project_root: Path | None = None) -> AppConfig:
    root = project_root or config_path.resolve().parent.parent
    with config_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    out = raw["output"]
    col = raw["collection"]
    flt = raw["filter"]
    exp = raw["export"]
    sent = raw.get("sentiment") or {}

    raw_dir = out.get("raw_json_dir")

    # Backward compatibility with older config key names
    results_per_query = col.get("results_per_query")
    if results_per_query is None:
        pages = int(col.get("max_pages_per_query", 2))
        results_per_query = pages * 50

    min_total = col.get("min_total_rows", col.get("min_rows", 100))

    return AppConfig(
        output=OutputConfig(
            csv_path=_path(out["csv_path"], root),
            manifest_path=_path(out["manifest_path"], root),
            raw_json_dir=_path(raw_dir, root) if raw_dir else None,
        ),
        collection=CollectionConfig(
            results_per_query=int(results_per_query),
            min_total_rows=int(min_total),
            sleep_ms_between_search=int(col["sleep_ms_between_search"]),
            order=str(col["order"]),
            relevance_language=str(col["relevance_language"]),
            safe_search=str(col["safe_search"]),
            video_category_id=(
                str(col["video_category_id"]) if col.get("video_category_id") else None
            ),
        ),
        queries=list(raw["queries"]),
        filter=FilterConfig(
            min_relevance_score=float(flt["min_relevance_score"]),
            educational_keywords=[str(k).lower() for k in flt["educational_keywords"]],
        ),
        export=ExportConfig(description_max_chars=int(exp["description_max_chars"])),
        sentiment=SentimentConfig(
            enabled=bool(sent.get("enabled", False)),
            output_csv_path=_path(
                sent.get("output_csv_path", "data/exports/educational_videos_with_sentiment.csv"),
                root,
            ),
        ),
        config_path=config_path.resolve(),
    )
