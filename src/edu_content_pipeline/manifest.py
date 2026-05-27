from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RunManifest:
    started_at_utc: str
    config_path: str
    queries: list[str]
    results_per_query: int = 100
    expected_raw_rows: int = 0
    per_query_counts: dict[str, int] = field(default_factory=dict)
    finished_at_utc: str | None = None
    raw_rows_before_dedupe: int = 0
    unique_video_ids: int = 0
    rows_after_filter: int = 0
    csv_path: str = ""
    quota_units_estimated: int = 0
    status: str = "running"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
