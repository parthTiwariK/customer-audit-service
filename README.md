# Customer Audit Service

Case Quality Audit repository with configurable questionnaires (Python FastAPI + MySQL + React).

## Quick start

1. Create a MySQL database (e.g. `case_audit`).
2. Copy `.env.example` to `.env` and set `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
3. Create a **Python venv** and install deps (do not use Homebrew `alembic` — that is a different program). macOS **3.9** works; **3.11+** is recommended:

```bash
cd customer-audit-service
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -e ".[dev]"   # or: pip install alembic sqlalchemy PyMySQL fastapi uvicorn pydantic pydantic-settings itsdangerous python-multipart
```

4. Run migrations and API (always use `python -m alembic` inside the venv):

```bash
cd backend
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8002
```

5. Frontend (dev):

```bash
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** (proxied to API on 8002) or build and serve from API:

```bash
npm run build
# then open http://localhost:8002
```

## Docker

```bash
cp .env.example .env
docker compose --profile migrate run --rm migrate
docker compose up --build api
```

API on **http://localhost:8002** (Gunicorn; set MySQL in `.env`). Ops: [RUNBOOK.md](RUNBOOK.md), [PERFORMANCE.md](PERFORMANCE.md).

## Features (P0)

- **Audit Search** default landing — filters, server pagination (25/50/100), sorting
- **New audit** — 15-question Case Quality template, backend scoring, one audit per Case ID
- **Audit detail** — full responses
- **Dashboard** — basic counts and averages

## Auth

- `AUTH_MODE=dev` (default) — automatic dev user
- `AUTH_MODE=local` — `POST /api/v1/auth/login` with `LOCAL_AUTH_USERNAME` / `LOCAL_AUTH_PASSWORD`

## Tests

```bash
pytest
```

Uses in-memory SQLite (no MySQL required for unit tests).