"""Metadata parsing for already-fetched static HTML."""

# pyright: basic

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urljoin

from lxml import html

from apps.previews.policies import UrlPolicyError, validate_external_url


@dataclass(frozen=True)
class PageMetadata:
    title: str | None
    description: str | None
    thumbnail_url: str | None
    canonical_url: str
    material_type: str


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    compact = " ".join(value.split())
    return compact or None


def _first(values: Iterable[str | None]) -> str | None:
    for value in values:
        cleaned = _clean(value)
        if cleaned is not None:
            return cleaned
    return None


def _meta_values(document: html.HtmlElement, names: tuple[str, ...]) -> list[str | None]:
    values: list[str | None] = []
    for name in names:
        values.extend(document.xpath(f"//meta[@property={name!r}]/@content"))
        values.extend(document.xpath(f"//meta[@name={name!r}]/@content"))
    return values


def _safe_absolute_url(candidate: str | None, base_url: str) -> str | None:
    if candidate is None:
        return None
    try:
        return validate_external_url(urljoin(base_url, candidate)).value
    except UrlPolicyError:
        return None


def parse_metadata(content: bytes, *, final_url: str) -> PageMetadata:
    """Return normalized preview fields without executing or retaining page scripts."""
    document = html.fromstring(content, base_url=final_url)
    canonical_candidate = _first(document.xpath("//link[@rel='canonical']/@href"))
    canonical_url = _safe_absolute_url(canonical_candidate, final_url) or final_url
    title = _first(
        [
            *_meta_values(document, ("og:title", "twitter:title")),
            *document.xpath("//title/text()"),
            *document.xpath("//h1[1]//text()"),
        ]
    )
    description = _first(
        _meta_values(document, ("og:description", "twitter:description", "description"))
    )
    thumbnail_url = _safe_absolute_url(
        _first(_meta_values(document, ("og:image", "twitter:image"))), final_url
    )
    og_type = _first(_meta_values(document, ("og:type",)))
    material_type = "video" if og_type == "video" else "article"
    return PageMetadata(title, description, thumbnail_url, canonical_url, material_type)
