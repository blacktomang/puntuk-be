# puntuk-be

Optional, authenticated preview enrichment for the stop-tumpuk PWA. It never
stores frontend learning data and capture remains fully local-first.

## Local development

Use Python 3.13 or later. Create a virtual environment and install the project
with its development dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
pip install --no-deps -e '.[dev]'
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

`GET /healthz` returns `{"status":"ok"}`. For PostgreSQL-backed container
development, copy `.env.example` to `.env` and run `docker compose up --build`.

## Checks

```bash
ruff check .
ruff format --check .
pyright
pytest
```

Production requires `DJANGO_DEBUG=false`, `DJANGO_SECRET_KEY`,
`DJANGO_ALLOWED_HOSTS`, trusted CSRF/CORS origins, and a PostgreSQL
`DATABASE_URL`. It also requires Google OAuth credentials, SMTP delivery
configuration, and a shared production cache for cross-worker rate limits.

## API boundary

- `POST /v1/auth/register`, `/login`, `/logout`, `/password-reset`, and the
  reset-confirmation route provide local username/password accounts.
- `GET /v1/auth/session` reports browser-session state. Authenticated users can
  start explicit Google linking at `GET /v1/auth/google/link`; ordinary Google
  OAuth begins at the configured `v1/auth/social/` route and never silently
  merges a local account by email.
- `POST /v1/previews` requires a session and accepts `{ "url": "https://…" }`.
  It returns safe preview metadata and an optional word-count estimate. Link
  capture must continue locally when this API is unavailable.

The preview service never stores frontend learning data, fetched HTML, or
article text. It only requests static public HTML; scripts, paywalls,
authenticated pages, and browser-rendered sites are outside its scope.

## Production release checklist

Run `python manage.py migrate`, then the checks above, before deploying. Put
the API behind HTTPS with egress rules that block private infrastructure and
cloud metadata endpoints. Configure PostgreSQL backups and test password-reset
mail plus Google callbacks using the production app/API origins. The frontend
is a separate repository; its IndexedDB/export migration and physical-device
PWA validation are release gates outside this service.
