#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  echo "[venv] creando entorno virtual .venv"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[venv] actualizando herramientas base"
python -m pip install --upgrade pip wheel setuptools

echo "[venv] instalando dependencias API"
pip install -r api/requirements.txt

echo "[venv] instalando dependencias de desarrollo"
pip install -r requirements-dev.txt

echo "[venv] verificando imports runtime"
python -c "import fastapi; import uvicorn; import sqlalchemy"

echo "[venv] verificando imports test"
python -c "import pytest; import httpx"

echo "[venv] entorno listo"
