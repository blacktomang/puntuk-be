"""Allowlisted video-provider runtime lookup; user URLs never become API URLs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib.parse import parse_qs, urlsplit

import httpx

YOUTUBE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
_DURATION = re.compile(
    r"^P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


@dataclass(frozen=True)
class VideoRuntime:
    seconds: int
    provenance: str = "api-runtime"
    completeness: str = "full"


class ProviderClient(Protocol):
    async def get(self, endpoint: str, *, params: dict[str, str]) -> Any: ...


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
    client: ProviderClient | None = None,
) -> VideoRuntime | None:
    video_id = youtube_video_id(raw_url)
    if not video_id or not api_key:
        return None
    owned_client = client is None
    http_client = client or httpx.AsyncClient(timeout=httpx.Timeout(5.0), follow_redirects=False)
    try:
        response = await http_client.get(
            YOUTUBE_API_ENDPOINT,
            params={"part": "contentDetails", "id": video_id, "key": api_key},
        )
        if response.status_code != 200:
            return None
        body: Any = response.json()
        body_map = cast(dict[str, Any], body) if isinstance(body, dict) else {}
        items = cast(list[dict[str, Any]], body_map.get("items", []))
        duration = items[0].get("contentDetails", {}).get("duration") if items else None
        seconds = parse_iso8601_duration(duration) if isinstance(duration, str) else None
        return VideoRuntime(seconds) if seconds is not None else None
    except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError):
        return None
    finally:
        if owned_client:
            await http_client.aclose()  # type: ignore[union-attr]
