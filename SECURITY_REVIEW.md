# Preview-fetch security review

Reviewed against the backend task checklist after the guarded JSON provider
transport was added.

- URL validation permits only HTTP(S), rejects user-info, and limits ports to
  80/443. Fragments are removed before requests.
- DNS answers are resolved before every request and redirect target. Every
  address is checked with `ipaddress` and non-global IPv4/IPv6, loopback,
  link-local, multicast, reserved, and private ranges are rejected.
- Redirects are manual and bounded. Responses are streamed through a byte cap,
  require the expected content type, and use a hard timeout.
- The httpx transport disables environment proxy variables (`trust_env=False`)
  so a developer or pod proxy cannot bypass the application’s target checks.
- The YouTube API URL is a fixed allowlisted endpoint; submitted material URLs
  are never interpolated into a provider endpoint. Provider JSON uses the same
  guarded DNS/timeout/size transport.
- Views return stable coarse failure categories and log only status plus the
  authenticated user identifier; raw URLs, HTML, article text, credentials,
  cookies, and reset tokens are not logged or persisted.

The application validates DNS before connecting, but the default httpx resolver
can theoretically observe a different answer after validation. Production
egress policy must therefore independently deny private ranges and cloud
metadata endpoints; a future pinned-resolution transport can tighten this
further without changing the API contract.
