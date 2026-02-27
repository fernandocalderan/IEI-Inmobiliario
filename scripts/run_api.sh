#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".env" ]; then
  # shellcheck disable=SC1091
  set -a
  source .env
  set +a
fi

if [ -z "${DATABASE_URL:-}" ] && [ -n "${DB_URL:-}" ]; then
  export DATABASE_URL="$DB_URL"
fi

API_PORT="${API_PORT:-8000}"

if [ ! -f ".venv/bin/activate" ]; then
  echo "[api] ERROR: no existe .venv. Ejecuta scripts/bootstrap_venv.sh"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[api] iniciando FastAPI en puerto $API_PORT"
echo "[api] health: http://localhost:$API_PORT/health"
echo "[api] docs:   http://localhost:$API_PORT/docs"

uvicorn api.main:app --host 0.0.0.0 --port "$API_PORT" --reload
