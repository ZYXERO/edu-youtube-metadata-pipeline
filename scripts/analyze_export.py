"""Quick summary stats for the exported CSV. Usage: python scripts/analyze_export.py"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "exports" / "educational_videos.csv"


def main() -> int:
    if not CSV_PATH.exists():
        print(f"Missing {CSV_PATH}. Run collect first.")
        return 1

    df = pd.read_csv(CSV_PATH)
    print(f"Rows: {len(df)}")
    print(f"Unique channels: {df['channel_title'].nunique()}")
    print("\nRows per search_query:")
    print(df["search_query"].value_counts().to_string())
    if "caption_available" in df.columns:
        cap = df["caption_available"].astype(str).str.lower() == "true"
        print(f"\nCaption available: {cap.sum()} ({100 * cap.mean():.1f}%)")
    if "duration_seconds" in df.columns:
        print(f"\nMedian duration (seconds): {df['duration_seconds'].median():.0f}")
    if "view_count" in df.columns:
        print(f"Median views: {df['view_count'].median():.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
