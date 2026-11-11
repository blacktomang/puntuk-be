# Backend contributor guidance

## Read first

Read [PLAN.md](PLAN.md), [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md),
[TECH_STACK.md](TECH_STACK.md), and [TASKS.md](TASKS.md) before changing this
service. The frontend product requirements remain authoritative for user
behavior: the backend is optional enrichment, not a source of truth for a
user's learning plan.

## Non-negotiable product boundaries

- Link saving works without an account, internet connection, or enrichment.
- Never persist fetched HTML, article text, notes, or frontend materials in
  this service.
- Do not add synchronization, analytics, AI inference, scraping through a
  generic proxy, browser automation, or paywall bypass as incidental work.
- Do not expose preview extraction to unauthenticated callers.
- Account data is limited to the authentication system and its operational
  records. Treat email addresses, sessions, submitted URLs, and logs as
  sensitive data.

## Engineering conventions

- Use strict Python type checking and explicit serializer/schema validation at
  HTTP, authentication, extraction, and persistence boundaries.
- Keep views thin. Put request validation, guarded fetching, metadata parsing,
  article extraction, and response mapping in separate testable modules.
- Route every remote URL through the guarded fetcher. Do not call `requests`,
  `httpx`, or library URL-download helpers directly from views or extractors.
- Model unknown duration as `null`; zero is a known explicit duration. Preserve
  provenance and completeness in API results.
- Treat remote HTML and metadata as untrusted. Do not render or return raw
  fetched HTML/text. Validate URLs before returning title images or canonical
  links.
- Keep secrets only in deployment environment variables or a secret manager;
  never commit SMTP credentials, Django secret keys, OAuth secrets, or live
  database URLs.
- Prefer small, purpose-built dependencies. Add a dependency only when its
  security and maintenance value outweighs code kept in this repository.

## Security review checklist

Changes touching fetching or authentication must verify:

- permitted schemes, DNS/IP classification, redirect revalidation, timeout,
  body-size, and content-type limits;
- session/cookie, CSRF, CORS, trusted-origin, and host configuration;
- account and IP rate limits, safe error responses, and no sensitive logs;
- URL, title, description, and image URL output validation;
- a test proving rejected input never initiates an unsafe external request.

## Verification

Run the narrowest checks that prove a change. At minimum, run formatting,
linting, type checking, and tests before handing off a completed milestone.
Changes to HTTP behavior require API integration tests. Changes to fetching
require SSRF and redirect tests. Changes to authentication require account-flow
tests. Do not report an unrun check as passing.

## Documentation and reporting

Update [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) when a module boundary, interface,
or security control changes; update [TECH_STACK.md](TECH_STACK.md) when a
dependency or runtime decision changes; and check items in [TASKS.md](TASKS.md)
only after implementation and verification. Report what changed, commands run,
and known limitations.

## Coding-agent collaboration

When a coding agent materially contributes to a change, preserve that
attribution in the commit message with a trailer such as
`Co-authored-by: Codex <codex@openai.com>`. Keep the human repository author as
the commit author, and describe agent-assisted work in the handoff when useful.
