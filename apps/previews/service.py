"""Preview orchestration; it returns metadata only and never persists source content."""

from __future__ import annotations

import asyncio
from typing import Any

from apps.previews.article import estimate_article_duration
from apps.previews.fetcher import GuardedFetcher, PreviewFetchError
from apps.previews.metadata import parse_metadata


def build_preview(url: str, *, fetcher: GuardedFetcher | None = None) -> dict[str, Any]:
    """Build a safe, best-effort preview response for one submitted URL."""
    guarded_fetcher = fetcher or GuardedFetcher()
    try:
        fetched = asyncio.run(guarded_fetcher.fetch_html(url))
    except PreviewFetchError as error:
        return {"status": "unavailable", "reason": error.failure.value}

    try:
        metadata = parse_metadata(fetched.content, final_url=fetched.url)
    except (TypeError, ValueError):
        return {"status": "unavailable", "reason": "not_extractable"}

    duration: dict[str, Any] = {
        "seconds": None,
        "provenance": "unknown",
        "completeness": "unknown",
    }
    if metadata.material_type == "article":
        estimate = estimate_article_duration(fetched.content, url=metadata.canonical_url)
        duration = {
            "seconds": estimate.seconds,
            "provenance": estimate.provenance,
            "completeness": estimate.completeness,
        }

    return {
        "status": "available",
        "finalUrl": metadata.canonical_url,
        "title": metadata.title,
        "description": metadata.description,
        "thumbnailUrl": metadata.thumbnail_url,
        "type": metadata.material_type,
        "duration": duration,
    }
