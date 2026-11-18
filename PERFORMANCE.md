# Customer Audit Service — Performance

How the API behaves under deploy, what was hardened, and how to re-measure. Pattern follows [eng-metrics PERFORMANCE.md](../komprise/productivity/reporting/eng-metrics/PERFORMANCE.md).

## 1. Architecture (deploy)

| Layer | Production | Dev |
|-------|------------|-----|
| Process | **Gunicorn** + `uvicorn.workers.UvicornWorker` (default 2 workers) | `uvicorn --reload` |
| DB | SQLAlchemy pool, `pool_recycle=280`, `pool_pre_ping` | Same |
| Edge | Optional nginx gzip + static cache ([sample](deploy/nginx.conf.sample)) | Vite proxy |
| Migrations | `docker compose --profile migrate` or CI job | Manual `alembic upgrade head` |

## 2. Hardening applied

| Change | Expected effect |
|--------|-----------------|
| `X-Response-Time` middleware | Separates server time from network in `curl` / `benchmark.py` |
| Search `submitted_at` filter uses **UTC datetime range** | Uses `ix_audits_submitted_at` instead of `func.date()` wrap |
| Gunicorn multi-worker | Concurrent auditors do not queue on a single uvicorn process |
| Alembic decoupled from app boot | Faster, safer container restarts on shared MySQL |
| `scripts/benchmark.py`, `loadtest.py`, `sysprobe.sh` | Repeatable measurement |

## 3. Hot paths (DB work per request)

| Endpoint | Queries | Notes |
|----------|---------|-------|
| `GET /api/v1/audits` | 2 | Count + page; `ILIKE '%x%'` still table-scan prone at large N |
| `GET /api/v1/audits/{id}` | 1 + joins | ~15 responses |
| `GET /api/v1/reports/summary` | ~5 | Acceptable until very large `audits` table |
| `GET /api/v1/questionnaires/latest` | 1 graph load | Small (15 questions) |

## 4. Acceptance targets

| Scenario | Target |
|----------|--------|
| Warm search (page 1, light filters) | Server p95 **&lt; 200 ms** on staging RDS |
| Warm audit detail | p95 **&lt; 150 ms** |
| Dashboard summary | p95 **&lt; 300 ms** at ≤10k audits |
| Load test 20 users / 30s | **0 errors**, warm p95 **&lt; 1 s** |

## 5. How to measure

```bash
# Start API (gunicorn or docker compose up api)
python scripts/benchmark.py --url http://127.0.0.1:8002 --warm 3 | tee benchmark.txt
python scripts/loadtest.py --url http://127.0.0.1:8002 --users 20 --duration 30 | tee loadtest.txt
```

Single request with server timing:

```bash
curl -s -o /dev/null -D - -w 'total: %{time_total}s\n' \
  'http://127.0.0.1:8002/api/v1/audits?page=1&page_size=25' | grep -i x-response-time
```

## 6. Measured results (fill after staging run)

_Record your environment (host type, MySQL host, row counts) and paste `benchmark.py` / `loadtest.py` output here._

| Run date | Environment | audits rows | audits_search warm | reports_summary warm | loadtest p95 |
|----------|-------------|-------------|--------------------|------------------------|--------------|
| _(pending)_ | | | | | |

## 7. Remaining bottlenecks (if data grows)

- Leading-wildcard `ILIKE` on search text fields
- Dashboard repeated aggregate queries — add short TTL cache if p95 exceeds target
- Run app in the **same region/VPC** as MySQL to avoid multi-ms RTT per query