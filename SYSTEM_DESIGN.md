# System design

## Architecture

```text
React PWA (app.<domain>)
  ├─ local IndexedDB: materials, notes, sessions, settings
  └─ authenticated POST /v1/previews
             │
             ▼
Django ASGI API (api.<domain>)
  ├─ Django auth + accounts API: users, sessions, password recovery
  ├─ social-auth-app-django: Google OAuth and linked identities
  ├─ preview API: request/response validation and rate limits
  ├─ guarded fetcher: URL, DNS/IP, redirect, size, type, timeout controls
  ├─ metadata parser: Open Graph, standard tags, JSON-LD, canonical URLs
  └─ extractor: Trafilatura → word count → duration result
             │
             ├─ PostgreSQL: authentication tables only
             ├─ SMTP: password-recovery mail
             └─ Google OAuth: external identity callback
```

The preview request is synchronous and best effort. It performs no durable
write except ordinary authentication/session activity. This ensures that a
retry cannot create or alter a frontend material.

## Django applications and module boundaries

```text
config/                 Django settings, ASGI, URLs, environment validation
apps/accounts/          custom user model, account API, recovery, Google links
apps/previews/
  api.py                authenticated HTTP endpoint and response mapping
  schemas.py            request/response schemas and validation
  service.py            preview orchestration; no HTTP framework imports
  fetcher.py            sole external-fetch capability and SSRF controls
  metadata.py           metadata extraction and normalization
  article.py            Trafilatura extraction and word-count calculation
  policies.py           host/IP/content and response-size policy helpers
  tests/                unit, API, and hostile-network fixtures
```

The preview service accepts a validated URL, calls the guarded fetcher, derives
metadata from the returned static HTML, and invokes the article extractor only
for valid HTML article candidates. It returns data objects, not Django response
objects. The API layer maps expected failures to the unavailable response; it
does not disclose internal host, resolver, or stack-trace details.

## Authentication and browser integration

Django's authentication system owns username/password hashes and sessions. A
small DRF accounts API exposes registration, login, logout, current session,
password-reset request, and password-reset confirmation. SMTP delivery is
configured by environment variables. `social-auth-app-django` owns the Google
OAuth protocol flow and provider identity persistence; it does not expose a
generic social-auth endpoint beyond configured providers.

The release does not require email verification. Google-created accounts need
a Google-verified, unused email. A direct Google login with an email belonging
to a local account must not silently link identities: the user signs in to the
local account and explicitly starts the link flow. Only authenticated sessions
may call preview extraction.

The browser uses secure, HttpOnly cookies scoped for the app/API site as
needed. Django validates `ALLOWED_HOSTS`, trusted CSRF origins, and the one
production PWA origin. CORS permits credentials only for explicit development
and production origins. Authentication rate limits and preview rate limits are
independent so a preview burst cannot weaken account protection.

## Preview extraction lifecycle

1. Validate the submitted URL syntax and HTTP(S) scheme.
2. Resolve the hostname and reject unsafe address classes before connecting.
3. Fetch without automatic redirects; validate and refetch each allowed hop,
   up to three redirects.
4. Require an HTML content type, stream no more than two MiB, and enforce an
   eight-second end-to-end deadline.
5. Parse title, description, preview image, canonical/final URL, and document
type from metadata without executing JavaScript.
6. For article candidates, run Trafilatura on in-memory HTML and URL context.
   Count language-aware word segments in its main text only; calculate seconds
   from the fixed 250-WPM assumption.
7. For known YouTube URLs, optionally call the fixed official YouTube Data API
   endpoint through the guarded JSON transport when `YOUTUBE_API_KEY` is
   configured; the submitted URL is never used as an API endpoint and an
   unavailable/quota-limited response remains unknown duration.
8. Discard source bytes and extracted text. Return normalized safe fields.

Source duration is nullable and has `api-runtime`, `publisher-estimate`,
`word-count`, `manual`, or `unknown` provenance plus `full`, `partial`, or
`unknown` completeness. This service never emits a manual override. A
description, thumbnail, or duration can be missing independently.

## Failure and privacy behavior

Network failures, robots/paywall/login pages, static-content absence,
JavaScript-only sites, unknown video runtime, parser failures, and quotas are
ordinary unavailable/partial outcomes. No response marks a frontend save as
failed. The service does not retain source bytes, article text, preview cache,
or frontend records. Logs use request IDs and coarse error categories; they
exclude raw URLs, HTML, email bodies, passwords, cookies, and token values.

## Operations

Deploy the stateless Django API separately from PostgreSQL with egress controls
that deny private infrastructure. Use a reverse proxy for TLS, request-size
limits, forwarded-host handling, and health endpoints. Apply Django migrations
for auth tables in a controlled deployment step and back up PostgreSQL. Keep
frontend IndexedDB/export migrations in the PWA repository; backend deploys do
not alter them.
