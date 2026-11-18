# Customer Audit Service — Operations

## Deploy (Docker)

1. Copy [`.env.example`](.env.example) to `.env` and set MySQL `DB_*` variables.
2. Run migrations **once** (or after schema changes):

```bash
docker compose --profile migrate run --rm migrate
```

3. Start the API (Gunicorn + 2 Uvicorn workers; **does not** run Alembic on boot):

```bash
docker compose up --build api
```

Open **http://localhost:8002**.

## Deploy (bare metal / VM)

```bash
cd customer-audit-service
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip setuptools wheel && pip install -e ".[dev]"
cp .env.example .env   # edit DB_*
cd backend && python -m alembic upgrade head
cd ..
export PYTHONPATH=backend
gunicorn -c deploy/gunicorn.conf.py app.main:app
```

Optional nginx: use [`deploy/nginx.conf.sample`](deploy/nginx.conf.sample).

### Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `CASE_AUDIT_BIND` | `0.0.0.0:8000` | Listen address |
| `CASE_AUDIT_WORKERS` | `2` (capped by CPU count) | Gunicorn workers |
| `RUN_MIGRATIONS` | `0` in prod | Set `1` only in migrate job / entrypoint |
| `AUTH_MODE` | `dev` | Use `local` or Entra in production |

## Performance checks

```bash
# API must be running; AUTH_MODE=dev for open API routes
python scripts/benchmark.py --url http://127.0.0.1:8002 --warm 3
python scripts/loadtest.py --url http://127.0.0.1:8002 --users 20 --duration 30
./scripts/sysprobe.sh   # optional; export DB_* from .env first
```

Record results in [PERFORMANCE.md](PERFORMANCE.md).

## Health

- `GET /health` — process up
- `GET /ready` — can reach MySQL
- Response header `X-Response-Time` — server-side latency (ms)

## Local development

Use `uvicorn` with reload (single worker):

```bash
cd backend
uvicorn app.main:app --reload --port 8002
```