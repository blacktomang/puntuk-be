from apps.previews.fetcher import FetchedHtml
from apps.previews.service import build_preview


class Fetcher:
    async def fetch_html(self, _: str) -> FetchedHtml:
        return FetchedHtml(
            url="https://example.test/article",
            content=(
                b"<article><h1>Useful article</h1><p>" + b"reading " * 300 + b"</p></article>"
            ),
            content_type="text/html",
        )


def test_preview_response_excludes_extracted_text() -> None:
    result = build_preview("https://example.test/article", fetcher=Fetcher())  # type: ignore[arg-type]

    assert result["status"] == "available"
    assert result["title"] == "Useful article"
    assert result["duration"] == {
        "seconds": 120,
        "provenance": "word-count",
        "completeness": "full",
    }
    assert "reading reading" not in str(result)
