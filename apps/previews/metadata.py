"""Metadata parsing for already-fetched static HTML."""

# pyright: basic

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

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


def _json_ld_values(document: html.HtmlElement) -> tuple[str | None, str | None, str | None]:
    """Read conservative title/description/image hints from JSON-LD blocks."""
    title: str | None = None
    description: str | None = None
    image: str | None = None
    for raw in document.xpath("//script[@type='application/ld+json']/text()"):
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError):
            continue
        candidates = payload if isinstance(payload, list) else [payload]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if title is None and isinstance(candidate.get("headline"), str):
                title = candidate["headline"]
            if title is None and isinstance(candidate.get("name"), str):
                title = candidate["name"]
            if description is None and isinstance(candidate.get("description"), str):
                description = candidate["description"]
            candidate_image = candidate.get("image")
            if image is None and isinstance(candidate_image, str):
                image = candidate_image
            if (
                image is None
                and isinstance(candidate_image, dict)
                and isinstance(candidate_image.get("url"), str)
            ):
                image = candidate_image["url"]
    return title, description, image


def parse_metadata(content: bytes, *, final_url: str) -> PageMetadata:
    """Return normalized preview fields without executing or retaining page scripts."""
    document = html.fromstring(content, base_url=final_url)
    json_ld_title, json_ld_description, json_ld_image = _json_ld_values(document)
    canonical_candidate = _first(document.xpath("//link[@rel='canonical']/@href"))
    canonical_url = _safe_absolute_url(canonical_candidate, final_url) or final_url
    title = _first(
        [
            *_meta_values(document, ("og:title", "twitter:title")),
            json_ld_title,
            *document.xpath("//title/text()"),
            *document.xpath("//h1[1]//text()"),
        ]
    )
    description = _first(
        [
            *_meta_values(document, ("og:description", "twitter:description", "description")),
            json_ld_description,
        ]
    )
    thumbnail_url = _safe_absolute_url(
        _first([*_meta_values(document, ("og:image", "twitter:image")), json_ld_image]), final_url
    )
    og_type = _first(_meta_values(document, ("og:type",)))
    host = (urlsplit(final_url).hostname or "").lower().removeprefix("www.")
    is_youtube = host in {"youtube.com", "m.youtube.com", "youtu.be"}
    material_type = "video" if og_type == "video" or is_youtube else "article"
    return PageMetadata(title, description, thumbnail_url, canonical_url, material_type)
