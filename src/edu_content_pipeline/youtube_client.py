from __future__ import annotations

import logging
import time
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SEARCH_QUOTA_COST = 100
VIDEOS_QUOTA_COST = 1


def _retryable_http_error(exc: BaseException) -> bool:
    if not isinstance(exc, HttpError):
        return False
    status = exc.resp.status if exc.resp else 0
    return status in (429, 500, 502, 503, 504)


class YouTubeClient:
    def __init__(self, api_key: str) -> None:
        self._youtube = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
        self.quota_units_used = 0

    def _charge(self, units: int, operation: str) -> None:
        self.quota_units_used += units
        logger.debug("Quota +%s (%s), total=%s", units, operation, self.quota_units_used)

    @retry(
        retry=retry_if_exception(_retryable_http_error),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def search_videos(
        self,
        query: str,
        *,
        max_results: int = 50,
        page_token: str | None = None,
        order: str = "relevance",
        relevance_language: str = "en",
        safe_search: str = "moderate",
        video_category_id: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": order,
            "relevanceLanguage": relevance_language,
            "safeSearch": safe_search,
        }
        if page_token:
            params["pageToken"] = page_token
        if video_category_id:
            params["videoCategoryId"] = video_category_id

        response = self._youtube.search().list(**params).execute()
        self._charge(SEARCH_QUOTA_COST, "search.list")
        return response

    @retry(
        retry=retry_if_exception(_retryable_http_error),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def get_video_details(self, video_ids: list[str]) -> list[dict[str, Any]]:
        if not video_ids:
            return []
        response = (
            self._youtube.videos()
            .list(part="snippet,statistics,contentDetails", id=",".join(video_ids))
            .execute()
        )
        self._charge(VIDEOS_QUOTA_COST, "videos.list")
        return response.get("items", [])


def sleep_ms(ms: int) -> None:
    if ms > 0:
        time.sleep(ms / 1000.0)
