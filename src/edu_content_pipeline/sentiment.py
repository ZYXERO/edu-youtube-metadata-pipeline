from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from edu_content_pipeline.normalize import CSV_COLUMNS, SENTIMENT_COLUMNS

logger = logging.getLogger(__name__)

MODEL_NAME = "vader_lexicon"
NEUTRAL_BAND = 0.05


def _ensure_vader() -> Any:
    try:
        import nltk
        from nltk.sentiment import SentimentIntensityAnalyzer
    except ImportError as exc:
        raise ImportError("Install nltk: pip install nltk") from exc

    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        logger.info("Downloading VADER lexicon (first run only)...")
        nltk.download("vader_lexicon", quiet=True)

    return SentimentIntensityAnalyzer()


def _label_from_compound(compound: float) -> str:
    if compound >= NEUTRAL_BAND:
        return "positive"
    if compound <= -NEUTRAL_BAND:
        return "negative"
    return "neutral"


def _score_text(analyzer: Any, text: str | None) -> tuple[str, float]:
    if not text or not str(text).strip():
        return "neutral", 0.0
    compound = analyzer.polarity_scores(str(text))["compound"]
    return _label_from_compound(compound), round(compound, 4)


def enrich_csv_with_sentiment(input_path: Path, output_path: Path) -> int:
    df = pd.read_csv(input_path)
    analyzer = _ensure_vader()

    title_results = df["title"].apply(lambda t: _score_text(analyzer, t))
    desc_results = df["description"].apply(lambda t: _score_text(analyzer, t))

    df["sentiment_title_label"] = title_results.apply(lambda x: x[0])
    df["sentiment_title_score"] = title_results.apply(lambda x: x[1])
    df["sentiment_description_label"] = desc_results.apply(lambda x: x[0])
    df["sentiment_description_score"] = desc_results.apply(lambda x: x[1])
    df["sentiment_combined_score"] = (
        (df["sentiment_title_score"].fillna(0) + df["sentiment_description_score"].fillna(0)) / 2
    ).round(4)
    df["sentiment_model"] = MODEL_NAME

    columns = [c for c in CSV_COLUMNS if c in df.columns]
    columns += [c for c in SENTIMENT_COLUMNS if c in df.columns]
    extra = [c for c in df.columns if c not in columns]
    df = df[columns + extra]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Wrote %s rows with sentiment to %s", len(df), output_path)
    return len(df)
