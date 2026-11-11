# stop-tumpuk backend plan

## Purpose

This service adds optional, authenticated link-preview enrichment to the
stop-tumpuk PWA. It provides chat-style metadata (title, description,
thumbnail, and final URL) and a best-effort article word count for estimating
reading time.

It does **not** own or synchronize learning materials, notes, sessions,
settings, or completion history. Those remain local-first in the existing
React PWA. A failed or unavailable backend must never prevent a user from
saving a link.

## Chosen approach

- **Runtime:** Python with Django ASGI and Django REST Framework.
- **Authentication:** Django's built-in authentication with a small accounts
  API, PostgreSQL, username/password accounts, password recovery through
  configurable SMTP, and Google OAuth through `social-auth-app-django`.
- **Extraction:** static-HTML fetches only. Parse Open Graph/standard/JSON-LD
  metadata first, then use Trafilatura to extract main article text and derive
  a language-aware word count.
- **Privacy:** return extracted metadata to the caller and immediately discard
  fetched HTML and article text. Do not cache previews or store user material
  data on the server.
- **Deployment:** serve the PWA at `app.<domain>` and the API at
  `api.<domain>`. The services use HTTPS, explicit trusted origins, secure
  cookies, and narrowly scoped credentialed CORS.

## Public interface

`POST /v1/previews` requires an authenticated browser session and accepts:

```json
{ "url": "https://example.com/article" }
```

It returns a successful partial preview or a truthful unavailable result. A
successful response contains only safe, normalized fields:

```json
{
  "status": "available",
  "finalUrl": "https://example.com/article",
  "title": "Example article",
  "description": "Optional summary",
  "thumbnailUrl": "https://example.com/image.jpg",
  "type": "article",
  "duration": {
    "seconds": 720,
    "provenance": "word-count",
    "completeness": "full"
  }
}
```

`status: "unavailable"` responses carry a stable, non-sensitive reason such
as `unsupported`, `blocked`, `not_html`, `too_large`, `timeout`, `paywalled`,
or `not_extractable`. They are normal enrichment outcomes, not capture errors.

## Account behavior

Registration creates a local account with a unique username, a unique recovery
email, and a Django-managed password hash. The initial release does not send
email-verification messages. Password reset uses the account's recovery email
and SMTP.

Google OAuth is an alternate sign-in method, not a replacement for a local
account. A Google subject already linked to an account signs into that account.
For a new Google subject, create an account only when Google supplies a
verified, unused email. When that email belongs to an existing local account,
ask the user to sign in with username/password and explicitly link Google from
account settings; never silently merge accounts by email.

## Safety boundary

All external fetching goes through one guarded client. It permits HTTP(S)
only; rejects loopback, private, link-local, multicast, and reserved addresses;
validates each redirect target; limits redirects to three; caps elapsed time at
eight seconds and HTML at two MiB; accepts HTML only; and runs with no internal
network access. The endpoint is rate-limited by authenticated account and IP.

The application does not execute page scripts, use a headless browser, bypass
paywalls, or fetch content from authenticated sessions. Client-rendered pages
may receive metadata only or an unavailable result.

## Frontend contract

The PWA will retain its save-first behavior. When signed in and online, it can
request a preview after persisting the material. It maps returned title,
thumbnail, type, and source duration into the existing material model while
preserving a manually corrected estimate. It adds a nullable local
`description` field through a versioned IndexedDB/export migration. Accounts
authorize enrichment only; signing in must not imply cross-device sync.
