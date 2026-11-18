#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ ! -d .venv ]]; then
  echo "Create .venv first: python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'"
  exit 1
fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
cd "$ROOT/backend"
python -m alembic upgrade head
echo "Migrations applied."