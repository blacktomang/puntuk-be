"""Allowlisted video-provider runtime lookup; user URLs never become API URLs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib.parse import parse_qs, urlsplit

from apps.previews.fetcher import PreviewFetchError

YOUTUBE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
_DURATION = re.compile(
    r"^P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


@dataclass(frozen=True)
class VideoRuntime:
    seconds: int
    provenance: str = "api-runtime"
    completeness: str = "full"


class JsonFetcher(Protocol):
    async def fetch_json(self, raw_url: str, *, params: dict[str, str]) -> dict[str, object]: ...


def youtube_video_id(raw_url: str) -> str | None:
    parsed = urlsplit(raw_url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if host == "youtu.be":
        candidate = parsed.path.strip("/").split("/", 1)[0]
        return candidate or None
    if host not in {"youtube.com", "m.youtube.com"}:
        return None
    if parsed.path == "/watch":
        return parse_qs(parsed.query).get("v", [None])[0]
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
        return parts[1] or None
    return None


def parse_iso8601_duration(value: str) -> int | None:
    match = _DURATION.fullmatch(value)
    if match is None:
        return None
    parts = {key: int(raw or 0) for key, raw in match.groupdict().items()}
    return (
        parts["days"] * 86_400 + parts["hours"] * 3_600 + parts["minutes"] * 60 + parts["seconds"]
    )


async def fetch_youtube_runtime(
    raw_url: str,
    api_key: str,
    *,
    fetcher: JsonFetcher,
) -> VideoRuntime | None:
    video_id = youtube_video_id(raw_url)
    if not video_id or not api_key:
        return None
    try:
        body = await fetcher.fetch_json(
            YOUTUBE_API_ENDPOINT,
            params={"part": "contentDetails", "id": video_id, "key": api_key},
        )
        items = cast(list[dict[str, Any]], body.get("items", []))
        duration = items[0].get("contentDetails", {}).get("duration") if items else None
        seconds = parse_iso8601_duration(duration) if isinstance(duration, str) else None
        return VideoRuntime(seconds) if seconds is not None else None
    except (PreviewFetchError, ValueError, TypeError, KeyError, IndexError):
        return None
