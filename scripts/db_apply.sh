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

DB_URL="${DB_URL:-${DATABASE_URL:-}}"
if [ -z "$DB_URL" ]; then
  echo "[db] ERROR: define DB_URL o DATABASE_URL en entorno/.env"
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "[db] ERROR: psql no está instalado en este sistema"
  exit 1
fi

PSQL_URL="${DB_URL/postgresql+psycopg:\/\//postgresql://}"
PSQL_URL="${PSQL_URL/postgresql+psycopg2:\/\//postgresql://}"

MIGRATION_SQL_001="db/migrations/001_init.sql"
SEED_SQL_001="db/seed/001_zones.sql"
MIGRATION_SQL_002="db/migrations/002_commercial_ops.sql"
SEED_SQL_002="db/seed/002_agencies_seed.sql"

if [ ! -f "$MIGRATION_SQL_001" ] || [ ! -f "$SEED_SQL_001" ]; then
  echo "[db] ERROR: faltan SQL requeridos ($MIGRATION_SQL_001 / $SEED_SQL_001)"
  exit 1
fi

echo "[db] aplicando migración: $MIGRATION_SQL_001"
psql "$PSQL_URL" -v ON_ERROR_STOP=1 -f "$MIGRATION_SQL_001"

if [ -f "$MIGRATION_SQL_002" ]; then
  echo "[db] aplicando migración: $MIGRATION_SQL_002"
  psql "$PSQL_URL" -v ON_ERROR_STOP=1 -f "$MIGRATION_SQL_002"
fi

echo "[db] aplicando seed: $SEED_SQL_001"
psql "$PSQL_URL" -v ON_ERROR_STOP=1 -f "$SEED_SQL_001"

if [ -f "$SEED_SQL_002" ]; then
  echo "[db] aplicando seed: $SEED_SQL_002"
  psql "$PSQL_URL" -v ON_ERROR_STOP=1 -f "$SEED_SQL_002"
fi

echo "[db] ok: migración + seed aplicados"
