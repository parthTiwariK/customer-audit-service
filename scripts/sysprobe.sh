#!/usr/bin/env bash
# Host + optional MySQL table stats. Set MYSQL_PWD or pass .env loaded by caller.
set -euo pipefail

echo "=== host ==="
uname -a
sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo "ncpu: unknown"
if command -v vm_stat >/dev/null; then vm_stat | head -5; fi

if [ -n "${DB_HOST:-}" ] && [ -n "${DB_USER:-}" ] && [ -n "${DB_NAME:-}" ]; then
  echo "=== mysql tables (case_audit) ==="
  mysql -h"${DB_HOST}" -P"${DB_PORT:-3306}" -u"${DB_USER}" "${DB_NAME}" -e \
    "SHOW TABLE STATUS WHERE Name IN ('audits','audit_responses','questionnaire_versions');" 2>/dev/null \
    || echo "mysql client unavailable or connection failed"
fi