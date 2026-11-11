"""The sole outbound HTTP client for untrusted preview URLs."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from urllib.parse import urljoin

import httpx

from apps.previews.policies import (
    ExternalUrl,
    UrlPolicyError,
    ensure_public_address,
    is_html_content_type,
    validate_external_url,
)

MAX_REDIRECTS = 3
MAX_HTML_BYTES = 2 * 1024 * 1024
FETCH_TIMEOUT_SECONDS = 8.0
PREVIEW_USER_AGENT = "stop-tumpuk-preview/1.0"


class FetchFailure(StrEnum):
    UNSUPPORTED = "unsupported"
    BLOCKED = "blocked"
    TOO_MANY_REDIRECTS = "too_many_redirects"
    NOT_HTML = "not_html"
    TOO_LARGE = "too_large"
    TIMEOUT = "timeout"
    NETWORK = "network"
    HTTP_ERROR = "http_error"


class PreviewFetchError(Exception):
    """A stable, safe-to-return preview failure."""

    def __init__(self, failure: FetchFailure) -> None:
        self.failure = failure
        super().__init__(failure.value)


@dataclass(frozen=True)
class TransportResponse:
    """Response data after a bounded transport read; never expose raw errors."""

    status_code: int
    headers: dict[str, str]
    body: bytes


@dataclass(frozen=True)
class FetchedHtml:
    """Validated static HTML returned to the metadata and article parsers."""

    url: str
    content: bytes
    content_type: str


Resolver = Callable[[str, int], Awaitable[Sequence[str]]]


class BoundedTransport(Protocol):
    """Transport implementation which enforces its own streaming body cap."""

    async def get(
        self, url: str, *, timeout_seconds: float, max_bytes: int
    ) -> TransportResponse: ...


async def resolve_host(hostname: str, port: int) -> Sequence[str]:
    """Resolve a hostname without making an HTTP request."""

    records = await asyncio.to_thread(
        socket.getaddrinfo,
        hostname,
        port,
        socket.AF_UNSPEC,
        socket.SOCK_STREAM,
    )
    return tuple(dict.fromkeys(str(record[4][0]) for record in records))


class HttpxBoundedTransport:
    """httpx adapter with redirects disabled and streamed response limits."""

    async def get(self, url: str, *, timeout_seconds: float, max_bytes: int) -> TransportResponse:
        timeout = httpx.Timeout(timeout_seconds)
        try:
            async with (
                httpx.AsyncClient(
                    follow_redirects=False,
                    headers={
                        "User-Agent": PREVIEW_USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml",
                    },
                    timeout=timeout,
                ) as client,
                client.stream("GET", url) as response,
            ):
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > max_bytes:
                        raise PreviewFetchError(FetchFailure.TOO_LARGE)
                return TransportResponse(
                    status_code=response.status_code,
                    headers={key.lower(): value for key, value in response.headers.items()},
                    body=bytes(body),
                )
        except PreviewFetchError:
            raise
        except httpx.TimeoutException as error:
            raise PreviewFetchError(FetchFailure.TIMEOUT) from error
        except httpx.HTTPError as error:
            raise PreviewFetchError(FetchFailure.NETWORK) from error


class GuardedFetcher:
    """Fetch public HTML with URL, DNS, redirect, timeout, and size controls."""

    def __init__(
        self,
        *,
        resolver: Resolver = resolve_host,
        transport: BoundedTransport | None = None,
        max_redirects: int = MAX_REDIRECTS,
        max_bytes: int = MAX_HTML_BYTES,
        timeout_seconds: float = FETCH_TIMEOUT_SECONDS,
    ) -> None:
        self._resolver = resolver
        self._transport = transport or HttpxBoundedTransport()
        self._max_redirects = max_redirects
        self._max_bytes = max_bytes
        self._timeout_seconds = timeout_seconds

    async def fetch_html(self, raw_url: str) -> FetchedHtml:
        """Return bounded HTML after validating every DNS and redirect hop."""

        current = self._safe_url(raw_url)
        for redirect_count in range(self._max_redirects + 1):
            await self._ensure_public_target(current)
            response = await self._transport.get(
                current.value,
                timeout_seconds=self._timeout_seconds,
                max_bytes=self._max_bytes,
            )
            if len(response.body) > self._max_bytes:
                raise PreviewFetchError(FetchFailure.TOO_LARGE)

            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if location is None or redirect_count == self._max_redirects:
                    raise PreviewFetchError(FetchFailure.TOO_MANY_REDIRECTS)
                current = self._safe_url(urljoin(current.value, location))
                continue

            if response.status_code < 200 or response.status_code >= 300:
                raise PreviewFetchError(FetchFailure.HTTP_ERROR)
            content_type = response.headers.get("content-type")
            if not is_html_content_type(content_type):
                raise PreviewFetchError(FetchFailure.NOT_HTML)
            return FetchedHtml(
                url=current.value,
                content=response.body,
                content_type=content_type or "",
            )

        raise PreviewFetchError(FetchFailure.TOO_MANY_REDIRECTS)

    @staticmethod
    def _safe_url(raw_url: str) -> ExternalUrl:
        try:
            return validate_external_url(raw_url)
        except UrlPolicyError as error:
            raise PreviewFetchError(FetchFailure.UNSUPPORTED) from error

    async def _ensure_public_target(self, target: ExternalUrl) -> None:
        try:
            try:
                addresses: Sequence[str] = (str(ipaddress.ip_address(target.hostname)),)
            except ValueError:
                addresses = await self._resolver(target.hostname, target.port)
            if not addresses:
                raise UrlPolicyError("blocked")
            for address in addresses:
                ensure_public_address(address)
        except UrlPolicyError as error:
            raise PreviewFetchError(FetchFailure.BLOCKED) from error
        except (OSError, socket.gaierror) as error:
            raise PreviewFetchError(FetchFailure.NETWORK) from error
