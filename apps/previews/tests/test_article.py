from apps.previews.article import (
    ArticleDuration,
    count_wordlike_segments,
    estimate_article_duration,
)


def test_counts_unicode_wordlike_segments_without_whitespace_assumption() -> None:
    assert count_wordlike_segments("Read well, 你好世界!") == 6


def test_estimates_main_article_text_without_returning_it() -> None:
    body = " ".join(["reading"] * 300)
    html = f"<html><body><nav>ignore navigation</nav><article><p>{body}</p></article></body></html>"

    estimate = estimate_article_duration(html.encode(), url="https://example.test/article")

    assert estimate == ArticleDuration(300, 120, "word-count", "full")
    assert not hasattr(estimate, "text")


def test_returns_unknown_when_no_main_article_text_is_available() -> None:
    estimate = estimate_article_duration(
        b"<html><body><nav>Only navigation</nav></body></html>", url="https://example.test"
    )

    assert estimate == ArticleDuration(None, None, "unknown", "unknown")
