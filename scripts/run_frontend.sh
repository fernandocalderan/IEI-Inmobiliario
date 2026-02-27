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
API_BASE_URL="${API_BASE_URL:-http://localhost:${API_PORT}}"

cat > frontend/assets/runtime-config.js <<EOF
window.__API_BASE__ = "${API_BASE_URL}";
EOF

echo "[frontend] API_BASE_URL=${API_BASE_URL}"
echo "[frontend] sirviendo frontend en http://localhost:${FRONTEND_PORT}"
python3 -m http.server "$FRONTEND_PORT" -d frontend
