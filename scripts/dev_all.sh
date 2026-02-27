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

API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5500}"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "[dev] levantando postgres por docker compose"
  docker compose -f docker/docker-compose.yml up -d postgres
else
  echo "[dev] docker compose no disponible; se asume DB externa"
fi

if [ ! -f .venv/bin/activate ]; then
  echo "[dev] entorno .venv no existe; ejecutando bootstrap"
  bash scripts/bootstrap_venv.sh
fi

echo "[dev] aplicando migraciones + seed"
bash scripts/db_apply.sh

mkdir -p .run

echo "[dev] iniciando API"
bash scripts/run_api.sh > .run/api.log 2>&1 &
API_PID=$!

echo "[dev] iniciando Frontend"
bash scripts/run_frontend.sh > .run/frontend.log 2>&1 &
FE_PID=$!

cleanup() {
  echo "[dev] cerrando procesos..."
  kill "$API_PID" "$FE_PID" >/dev/null 2>&1 || true
}
trap cleanup INT TERM EXIT

echo "[dev] URLs"
echo "  Front:  http://localhost:${FRONTEND_PORT}"
echo "  API:    http://localhost:${API_PORT}/docs"
echo "  Admin:  http://localhost:${FRONTEND_PORT}/admin/login.html"
echo "[dev] logs: .run/api.log y .run/frontend.log"

wait "$API_PID" "$FE_PID"
