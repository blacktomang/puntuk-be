"""Focused tests for the guarded external-preview fetch boundary."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine, Sequence
from dataclasses import dataclass, field
from typing import Any

import pytest

from apps.previews.fetcher import (
    FetchFailure,
    GuardedFetcher,
    PreviewFetchError,
    TransportResponse,
)


async def public_resolver(_: str, __: int) -> Sequence[str]:
    return ("93.184.216.34",)


@dataclass
class FakeTransport:
    responses: dict[str, TransportResponse]
    calls: list[str] = field(default_factory=lambda: [])

    async def get(self, url: str, *, timeout_seconds: float, max_bytes: int) -> TransportResponse:
        del timeout_seconds, max_bytes
        self.calls.append(url)
        return self.responses[url]


def run[Result](coroutine: Coroutine[Any, Any, Result]) -> Result:
    return asyncio.run(coroutine)


def test_rejects_unsafe_scheme_before_request() -> None:
    transport = FakeTransport({})
    fetcher = GuardedFetcher(resolver=public_resolver, transport=transport)

    with pytest.raises(PreviewFetchError) as raised:
        run(fetcher.fetch_html("file:///etc/passwd"))

    assert raised.value.failure is FetchFailure.UNSUPPORTED
    assert transport.calls == []


def test_rejects_private_literal_before_request() -> None:
    transport = FakeTransport({})
    fetcher = GuardedFetcher(resolver=public_resolver, transport=transport)

    with pytest.raises(PreviewFetchError) as raised:
        run(fetcher.fetch_html("http://127.0.0.1/"))

    assert raised.value.failure is FetchFailure.BLOCKED
    assert transport.calls == []


def test_rejects_private_ipv6_literal_before_request() -> None:
    transport = FakeTransport({})
    fetcher = GuardedFetcher(resolver=public_resolver, transport=transport)

    with pytest.raises(PreviewFetchError) as raised:
        run(fetcher.fetch_html("http://[::1]/"))

    assert raised.value.failure is FetchFailure.BLOCKED
    assert transport.calls == []


def test_rejects_private_dns_answer_before_request() -> None:
    async def private_resolver(_: str, __: int) -> Sequence[str]:
        return ("10.0.0.8",)

    transport = FakeTransport({})
    fetcher = GuardedFetcher(resolver=private_resolver, transport=transport)

    with pytest.raises(PreviewFetchError) as raised:
        run(fetcher.fetch_html("https://example.test/article"))

    assert raised.value.failure is FetchFailure.BLOCKED
    assert transport.calls == []


def test_revalidates_redirect_target_before_following() -> None:
    async def resolver(hostname: str, _: int) -> Sequence[str]:
        return ("10.0.0.8",) if hostname == "internal.test" else ("93.184.216.34",)

    initial = "https://public.test/article"
    transport = FakeTransport(
        {initial: TransportResponse(302, {"location": "https://internal.test/secret"}, b"")},
    )
    fetcher = GuardedFetcher(resolver=resolver, transport=transport)

    with pytest.raises(PreviewFetchError) as raised:
        run(fetcher.fetch_html(initial))

    assert raised.value.failure is FetchFailure.BLOCKED
    assert transport.calls == [initial]


def test_rejects_non_html_response() -> None:
    url = "https://example.test/image.jpg"
    transport = FakeTransport(
        {url: TransportResponse(200, {"content-type": "image/jpeg"}, b"image")}
    )
    fetcher = GuardedFetcher(resolver=public_resolver, transport=transport)

    with pytest.raises(PreviewFetchError) as raised:
        run(fetcher.fetch_html(url))

    assert raised.value.failure is FetchFailure.NOT_HTML


def test_rejects_response_exceeding_bound() -> None:
    url = "https://example.test/article"
    transport = FakeTransport(
        {url: TransportResponse(200, {"content-type": "text/html"}, b"abcdef")}
    )
    fetcher = GuardedFetcher(resolver=public_resolver, transport=transport, max_bytes=5)

    with pytest.raises(PreviewFetchError) as raised:
        run(fetcher.fetch_html(url))

    assert raised.value.failure is FetchFailure.TOO_LARGE


def test_returns_bounded_html_with_normalized_url() -> None:
    url = "https://example.test"
    transport = FakeTransport(
        {
            "https://example.test/": TransportResponse(
                200, {"content-type": "text/html; charset=utf-8"}, b"<h1>ok</h1>"
            )
        },
    )
    fetcher = GuardedFetcher(resolver=public_resolver, transport=transport)

    response = run(fetcher.fetch_html(url))

    assert response.url == "https://example.test/"
    assert response.content == b"<h1>ok</h1>"


def test_fetches_provider_json_through_guarded_transport() -> None:
    endpoint = "https://api.example.test/runtime"
    request_url = endpoint + "?id=abc&part=contentDetails"
    transport = FakeTransport(
        {
            request_url: TransportResponse(
                200,
                {"content-type": "application/json"},
                b'{"items": []}',
            )
        }
    )
    fetcher = GuardedFetcher(resolver=public_resolver, transport=transport)

    response = run(fetcher.fetch_json(endpoint, params={"id": "abc", "part": "contentDetails"}))

    assert response == {"items": []}
    assert transport.calls == [request_url]
