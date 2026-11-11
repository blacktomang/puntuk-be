# puntuk-be

Optional, authenticated preview enrichment for the stop-tumpuk PWA. It never
stores frontend learning data and capture remains fully local-first.

## Local development

Use Python 3.13 or later. Create a virtual environment and install the project
with its development dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
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
`DATABASE_URL`.
