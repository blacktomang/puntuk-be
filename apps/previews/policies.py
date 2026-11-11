"""Pure validation rules for the preview fetch boundary."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit, urlunsplit


class UrlPolicyError(ValueError):
    """Raised when a URL cannot be safely requested by the preview service."""


@dataclass(frozen=True)
class ExternalUrl:
    """An HTTP(S) URL whose syntactic components passed local validation."""

    value: str
    hostname: str
    port: int


def validate_external_url(raw_url: str) -> ExternalUrl:
    """Allow only normal public-web URL syntax before DNS resolution."""

    try:
        parsed = urlsplit(raw_url)
    except ValueError as error:
        raise UrlPolicyError("unsupported") from error

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UrlPolicyError("unsupported")
    if parsed.username is not None or parsed.password is not None:
        raise UrlPolicyError("unsupported")

    try:
        port = parsed.port
    except ValueError as error:
        raise UrlPolicyError("unsupported") from error
    effective_port = port or (443 if parsed.scheme == "https" else 80)
    if effective_port not in {80, 443}:
        raise UrlPolicyError("unsupported")

    normalized = SplitResult(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc,
        path=parsed.path or "/",
        query=parsed.query,
        fragment="",
    )
    return ExternalUrl(
        value=urlunsplit(normalized),
        hostname=parsed.hostname.rstrip(".").lower(),
        port=effective_port,
    )


def ensure_public_address(address: str) -> None:
    """Reject every address not globally routable on the public Internet."""

    try:
        parsed = ipaddress.ip_address(address)
    except ValueError as error:
        raise UrlPolicyError("blocked") from error
    if not parsed.is_global:
        raise UrlPolicyError("blocked")


def is_html_content_type(content_type: str | None) -> bool:
    """Return whether a response declares one of the supported HTML types."""

    if content_type is None:
        return False
    media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
    return media_type in {"text/html", "application/xhtml+xml"}
