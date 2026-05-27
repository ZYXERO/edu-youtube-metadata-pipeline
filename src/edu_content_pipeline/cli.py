from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from edu_content_pipeline.collector import collect
from edu_content_pipeline.config import load_config
from edu_content_pipeline.sentiment import enrich_csv_with_sentiment
from edu_content_pipeline.youtube_client import YouTubeClient

logger = logging.getLogger(__name__)


def _find_project_root() -> Path:
    """Walk up from cwd to find directory containing config/default.yaml."""
    candidates = [Path.cwd(), Path(__file__).resolve().parents[2]]
    for base in candidates:
        if (base / "config" / "default.yaml").exists():
            return base
    return Path.cwd()


def cmd_collect(args: argparse.Namespace) -> int:
    root = _find_project_root()
    load_dotenv(root / ".env")

    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    placeholders = (
        "",
        "your_google_cloud_api_key_here",
        "AIzaSyDEMO_REPLACE_WITH_REAL_KEY_FROM_CONSOLE",
    )
    if api_key in placeholders:
        logger.error(
            "Set YOUTUBE_API_KEY in .env (see .env.example). Current value is missing or placeholder."
        )
        return 1

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path

    config = load_config(config_path, project_root=root)
    client = YouTubeClient(api_key=api_key)
    manifest = collect(config, client)

    logger.info(
        "Done: status=%s rows=%s quota_units=%s csv=%s",
        manifest.status,
        manifest.rows_after_filter,
        manifest.quota_units_estimated,
        manifest.csv_path,
    )

    if manifest.status != "success":
        return 1
    return 0


def cmd_sentiment(args: argparse.Namespace) -> int:
    root = _find_project_root()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    config = load_config(config_path, project_root=root)

    input_path = Path(args.input) if args.input else config.output.csv_path
    if not input_path.is_absolute():
        input_path = root / input_path

    output_path = Path(args.output) if args.output else config.sentiment.output_csv_path
    if not output_path.is_absolute():
        output_path = root / output_path

    if not input_path.exists():
        logger.error("Input CSV not found: %s (run collect first)", input_path)
        return 1

    enrich_csv_with_sentiment(input_path, output_path)
    logger.info("Sentiment enrichment complete: %s", output_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edu_content_pipeline",
        description="Collect education-related YouTube metadata to CSV (EnCoDe Lab Option B).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    collect_parser = sub.add_parser("collect", help="Run search, enrich, and export CSV")
    collect_parser.add_argument(
        "--config",
        default="config/default.yaml",
        help="Path to YAML config (default: config/default.yaml)",
    )
    collect_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    collect_parser.set_defaults(func=cmd_collect)

    sentiment_parser = sub.add_parser(
        "sentiment",
        help="Add VADER sentiment columns to an existing CSV (offline, no YouTube quota)",
    )
    sentiment_parser.add_argument("--config", default="config/default.yaml")
    sentiment_parser.add_argument(
        "--input",
        default=None,
        help="Input CSV (default: output.csv_path from config)",
    )
    sentiment_parser.add_argument(
        "--output",
        default=None,
        help="Output CSV (default: sentiment.output_csv_path from config)",
    )
    sentiment_parser.add_argument("-v", "--verbose", action="store_true")
    sentiment_parser.set_defaults(func=cmd_sentiment)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    level = logging.DEBUG if getattr(args, "verbose", False) else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
