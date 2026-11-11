# Technical stack

## Chosen stack

| Area | Choice | Rationale |
| --- | --- | --- |
| Language/runtime | Python, supported current CPython | Best ecosystem fit for web-content extraction while remaining straightforward to operate. |
| Web framework | Django ASGI | Mature security, settings, migrations, session handling, and admin/operational tooling. |
| HTTP API | Django REST Framework | Explicit serializer-based API validation and a broad Django integration ecosystem. |
| Authentication | Django auth + custom DRF account endpoints + `social-auth-app-django` | Small self-hosted username/password and session surface, with Google OAuth protocol support but no full account-suite dependency. |
| Database | PostgreSQL | Durable relational store for account/session data and production-ready backups. |
| Extraction | Trafilatura | Main-text extraction plus metadata support and fallback extraction strategies. |
| Outbound HTTP | httpx async client | Streaming limits and explicit redirect handling in the ASGI runtime. |
| HTML/metadata parsing | lxml/selectolax-compatible parser selected during implementation | Parse untrusted static HTML without a browser or JavaScript execution. |
| Background work | None in v1 | Preview is bounded synchronous best-effort work; no queue or cache is needed. |
| Mail | Configurable SMTP | User-controlled delivery provider or self-hosted relay. |
| Test | pytest, pytest-django, factory fixtures | Unit, integration, and hostile-input coverage. |
| Quality | Ruff, formatter, Pyright or mypy | Fast lint/format checks and strict typing at service boundaries. |
| Deployment | Containerized ASGI process behind HTTPS reverse proxy | Portable self-hosted deployment with controlled network egress. |

## Deliberate exclusions

- No cloud identity provider, hosted extraction API, generic CORS proxy, or
  paid AI dependency.
- No Playwright/Chromium extraction fallback, scraping login-gated content,
  paywall bypass, persistent preview cache, task queue, or crawler.
- No backend ownership of materials, notes, reading sessions, exports, or
  cross-device synchronization.
- No Go authentication library in the selected implementation. Go plus Ory
  Kratos remains a viable future architecture but would introduce a separate
  identity service and is not justified for this first backend.

## Environment configuration

Required deployment configuration includes Django secret key, production hosts
and trusted origins, PostgreSQL URL, SMTP connection and sender identity,
Google OAuth client ID/secret/redirect URI, secure-cookie settings, preview
rate-limit settings, and outbound fetch limits. Validate these settings at
startup and fail closed in production when security-critical values are absent.

Never place these values in the React build. The frontend receives only public
API/origin configuration.

## Dependency policy

Pin compatible package ranges in the lockfile, update security fixes promptly,
and inspect release notes for Django, `social-auth-app-django`, Trafilatura,
lxml/parser, and httpx changes. Prefer the standard library for URL and IP
classification where possible. A library that fetches arbitrary URLs must not
bypass the guarded fetcher.
