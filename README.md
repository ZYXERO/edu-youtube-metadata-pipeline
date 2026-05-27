# Educational YouTube Metadata Pipeline

[![Repository](https://img.shields.io/badge/GitHub-ZYXERO%2Fedu--youtube--metadata--pipeline-181717?logo=github)](https://github.com/ZYXERO/edu-youtube-metadata-pipeline)

**EnCoDe Lab (USF) — New Student Challenge, Option B**

Reproducible Python pipeline that searches YouTube for education-related videos and exports structured metadata to CSV (≥100 unique videos per run).

**Author:** [Kaushik Selvakumar](https://github.com/ZYXERO) · Computer Engineering, USF

## Status

**Working** — run `collect` to produce CSV + manifest (≥100 unique videos).

## Quick start

```powershell
cd edu-youtube-metadata-pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
copy .env.example .env             # then set YOUTUBE_API_KEY
python -m edu_content_pipeline collect --config config/default.yaml
python -m edu_content_pipeline sentiment --config config/default.yaml
python scripts/analyze_export.py   # optional summary stats
```

**Collection model:** each entry in `queries` collects up to **`results_per_query`** videos (default **100**). Five queries → up to **500** rows before dedupe; unique count is typically slightly lower.

**Outputs:** `data/exports/educational_videos.csv`, `data/exports/run_manifest.json`, optional `educational_videos_with_sentiment.csv`

**EnCoDe-themed queries** in `config/default.yaml` align with the lab’s HCI, AR, child-computer interaction, and learning-technology focus ([encoderesearchlab.org](https://encoderesearchlab.org/)).

## Architecture

```
CLI (collect / sentiment)
    → config (YAML queries, limits, paths)
    → youtube_client (search.list → video IDs; videos.list in batches of 50)
    → normalize, dedupe, optional relevance filter
    → export CSV + run_manifest.json
```

- **Discovery:** `search.list` per configured query (paginated).
- **Enrichment:** `videos.list` in chunks of 50 for statistics and metadata.
- **Reproducibility:** each run writes `run_manifest.json` (timestamp, queries, row counts, quota estimate).

## Platform choice

YouTube Data API v3 provides documented quotas, official Terms of Service, and rich public metadata (titles, descriptions, duration, captions flag, engagement) suitable for exploring how educational creators present learning content.

## Quota and limitations

- Default quota: **10,000 units/day**; `search.list` ≈ 100 units per call; `videos.list` is cheaper when batched.
- This pipeline favors few searches and many batch enrichment calls.
- Results reflect platform search ranking, not a complete census of educational YouTube; optional keyword relevance scoring is exploratory only.

## License / ethics

Public API metadata only. Respect [YouTube API Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service). Do not redistribute API responses beyond your submission context.
