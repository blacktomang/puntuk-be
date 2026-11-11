from apps.previews.metadata import parse_metadata


def test_parses_preview_metadata_with_safe_relative_thumbnail() -> None:
    result = parse_metadata(
        b"""
        <html><head>
          <meta property="og:title" content="  Useful article  ">
          <meta property="og:description" content="A concise explanation.">
          <meta property="og:image" content="/preview.jpg">
          <link rel="canonical" href="https://example.test/canonical">
        </head></html>
        """,
        final_url="https://example.test/original",
    )

    assert result.title == "Useful article"
    assert result.description == "A concise explanation."
    assert result.thumbnail_url == "https://example.test/preview.jpg"
    assert result.canonical_url == "https://example.test/canonical"


def test_rejects_unsafe_preview_image_url() -> None:
    result = parse_metadata(
        b"<meta property='og:image' content='file:///etc/passwd'>",
        final_url="https://example.test/article",
    )

    assert result.thumbnail_url is None


def test_uses_json_ld_after_open_graph_metadata() -> None:
    result = parse_metadata(
        b"""<script type="application/ld+json">
        {"headline":"Structured title","description":"Structured description",
         "image":{"url":"/structured.jpg"}}
        </script>""",
        final_url="https://example.test/article",
    )

    assert result.title == "Structured title"
    assert result.description == "Structured description"
    assert result.thumbnail_url == "https://example.test/structured.jpg"


def test_open_graph_precedes_json_ld() -> None:
    result = parse_metadata(
        b"""<meta property="og:title" content="Open Graph title">
        <script type="application/ld+json">{"headline":"Structured title"}</script>""",
        final_url="https://example.test/article",
    )

    assert result.title == "Open Graph title"


def test_malformed_html_still_returns_normalized_metadata() -> None:
    result = parse_metadata(b"<html><title>Unclosed", final_url="https://example.test/article")

    assert result.title == "Unclosed"
