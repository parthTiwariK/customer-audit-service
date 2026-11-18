#!/bin/sh
set -eu
cd /app
export PYTHONPATH=/app/backend:${PYTHONPATH:-}

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Running alembic upgrade head..."
  cd /app/backend && python -m alembic upgrade head
  cd /app
fi

exec gunicorn -c /app/deploy/gunicorn.conf.py app.main:app