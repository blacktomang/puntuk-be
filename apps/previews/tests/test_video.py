import asyncio

from apps.previews.video import fetch_youtube_runtime, parse_iso8601_duration, youtube_video_id


def test_extracts_supported_youtube_video_ids() -> None:
    assert youtube_video_id("https://youtu.be/abc123") == "abc123"
    assert youtube_video_id("https://www.youtube.com/watch?v=abc123") == "abc123"
    assert youtube_video_id("https://youtube.com/shorts/abc123") == "abc123"
    assert youtube_video_id("https://example.test/watch?v=abc123") is None


def test_parses_youtube_iso8601_runtime() -> None:
    assert parse_iso8601_duration("PT1H2M3S") == 3_723
    assert parse_iso8601_duration("PT0S") == 0
    assert parse_iso8601_duration("not-a-duration") is None


class Response:
    status_code = 200

    def json(self) -> dict[str, object]:
        return {"items": [{"contentDetails": {"duration": "PT12M3S"}}]}


class Client:
    def __init__(self) -> None:
        self.endpoint: str | None = None
        self.params: dict[str, str] | None = None

    async def get(self, endpoint: str, *, params: dict[str, str]) -> Response:
        self.endpoint = endpoint
        self.params = params
        return Response()


def test_runtime_uses_fixed_provider_endpoint() -> None:
    client = Client()

    runtime = asyncio.run(
        fetch_youtube_runtime("https://www.youtube.com/watch?v=abc123", "secret", client=client)
    )

    assert runtime is not None
    assert runtime.seconds == 723
    assert client.endpoint == "https://www.googleapis.com/youtube/v3/videos"
    assert client.params == {"part": "contentDetails", "id": "abc123", "key": "secret"}
