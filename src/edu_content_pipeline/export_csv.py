from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from edu_content_pipeline.normalize import CSV_COLUMNS


def export_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    for col in CSV_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[CSV_COLUMNS]
    df.to_csv(path, index=False, encoding="utf-8")
