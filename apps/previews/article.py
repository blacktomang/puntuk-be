"""In-memory article-duration extraction with no durable text output."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal

from trafilatura import extract

WORDS_PER_MINUTE = 250
MINIMUM_ESTIMABLE_WORDS = 25
_CJK_CHARACTER = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
_NON_CJK_WORD = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True)
class ArticleDuration:
    """Planning-only duration; extracted source text is intentionally omitted."""

    word_count: int | None
    seconds: int | None
    provenance: Literal["word-count", "unknown"]
    completeness: Literal["full", "unknown"]


def count_wordlike_segments(text: str) -> int:
    """Count Latin-like words and individual Han characters without whitespace assumptions."""
    han_characters = len(_CJK_CHARACTER.findall(text))
    without_han = _CJK_CHARACTER.sub(" ", text)
    return han_characters + len(_NON_CJK_WORD.findall(without_han))


def estimate_article_duration(html: bytes, *, url: str) -> ArticleDuration:
    """Extract static main text from provided HTML and return only its planning estimate."""
    text = extract(
        html.decode("utf-8", errors="replace"),
        url=url,
        output_format="txt",
        include_comments=False,
        include_tables=True,
    )
    if not text:
        return ArticleDuration(None, None, "unknown", "unknown")

    word_count = count_wordlike_segments(text)
    if word_count < MINIMUM_ESTIMABLE_WORDS:
        return ArticleDuration(None, None, "unknown", "unknown")
    return ArticleDuration(
        word_count=word_count,
        seconds=math.ceil(word_count / WORDS_PER_MINUTE) * 60,
        provenance="word-count",
        completeness="full",
    )
