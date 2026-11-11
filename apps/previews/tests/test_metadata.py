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
