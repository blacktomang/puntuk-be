# Deployment and recovery runbook

This service is an optional, stateless enrichment API. The React PWA remains
the source of truth for captures, materials, notes, sessions, and exports.

## Required production configuration

Set these as deployment secrets or environment variables; do not commit them:

- `DJANGO_DEBUG=false` and a long random `DJANGO_SECRET_KEY`.
- `DJANGO_ALLOWED_HOSTS` for the API host.
- `DJANGO_CSRF_TRUSTED_ORIGINS` and `DJANGO_CORS_ALLOWED_ORIGINS` for the HTTPS
  PWA origin; keep credentialed CORS limited to that origin.
- `DATABASE_URL` for PostgreSQL, plus `DJANGO_DEFAULT_FROM_EMAIL` and the SMTP
  connection variables used by password recovery.
- `GOOGLE_OAUTH2_CLIENT_ID` and `GOOGLE_OAUTH2_CLIENT_SECRET`, with the Google
  callback registered as `/v1/auth/social/complete/google-oauth2/` on the API
  origin. `YOUTUBE_API_KEY` is optional; without it video duration is unknown.

Terminate TLS at a reverse proxy, forward only the configured host, and route
`/healthz` and `/v1/` to the ASGI container. Permit outbound traffic only to
public web targets and the explicitly configured provider API; deny private
networks and cloud metadata addresses at the egress layer as a second control.

## Release procedure

1. Build the pinned image with `docker build -t puntuk-be:$GIT_SHA .`.
2. Run `python manage.py check --deploy` with production-like environment
   variables.
3. Run `python manage.py migrate` as a controlled release step against the
   backed-up PostgreSQL database.
4. Start the ASGI process, verify `/healthz`, then run account and preview API
   smoke tests over HTTPS.
5. Keep the previous image available until health checks and rollback tests
   succeed. Never clear the database to recover a failed release.

## Recovery and incident handling

Take PostgreSQL backups according to the hosting policy and test restoring one
before the first production release. For a failed deploy, stop promotion and
roll back the image only when its migrations remain compatible; otherwise
restore the database snapshot to an isolated instance and repair forward.
Rotate Django, OAuth, SMTP, and provider secrets after suspected exposure.
Review coarse request categories and rate-limit events without logging raw URLs,
HTML, article text, credentials, cookies, or reset tokens.

## Updates and known limits

Run the locked CI checks before dependency updates, review Django/httpx/
Trafilatura/social-auth security advisories, regenerate `requirements.lock`, and
deploy the resulting image through staging. Preview extraction is static HTML
only: JavaScript-rendered pages, authenticated content, paywalls, and blocked
origins can return partial or unavailable metadata. The service never stores
fetched HTML, article text, notes, or frontend materials, and it does not sync
the PWA across devices.
