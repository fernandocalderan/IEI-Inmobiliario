# IEI Inmobiliario MVP

MVP funcional (Fases 0-2) con:
- Motor IEI existente (`iei_engine.py`) sin cambios.
- API FastAPI (`/api`) con scoring, leads, admin, zonas, eventos y privacidad.
- Persistencia Postgres con SQL en `db/migrations` + seed en `db/seed`.
- Frontend vanilla (`/frontend`) con landing, wizard, resultado y admin básico.

## Requisitos

- Python 3.11+
- `psql` instalado para aplicar SQL desde host
- Docker + Docker Compose (opcional, recomendado para Postgres local)

## Variables de entorno

Copia y edita:

```bash
cp .env.example .env
```

Variables clave:

- `DB_URL` / `DATABASE_URL` (URL de base de datos)
- `API_PORT` (default `8000`)
- `FRONTEND_PORT` (default `5500`)
- `API_BASE_URL` (default `http://localhost:8000`)
- `ADMIN_PASSWORD`
- `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_LEADS_PER_MINUTE`
- `DEDUPE_WINDOW_DAYS`, `PHONE_HASH_SALT`
- `FEATURE_RESERVATIONS`, `EXPORT_PII`

## Quickstart (local)

```bash
make venv
make db-bootstrap
make dev
```

URLs esperadas:
- Front: `http://localhost:5500`
- API docs: `http://localhost:8000/docs`
- Admin: `http://localhost:5500/admin/login.html`

## Flujo por comandos

### 1) Instalar dependencias

```bash
make venv
```

### 2) Levantar Postgres

```bash
make db-up
```

### 3) Aplicar migraciones + seed

```bash
make db-apply
```

### 3b) Levantar Postgres + migración + seed (un comando)

```bash
make db-bootstrap
```

### 4) Levantar API

```bash
make api
```

### 5) Levantar frontend

```bash
make fe
```

### 6) Ejecutar tests

```bash
make test
```

### 7) Smoke E2E

```bash
make smoke
```

### 8) Tests + smoke E2E (un comando)

```bash
make verify
```

## Scripts operativos

- `scripts/bootstrap_venv.sh`
- `scripts/db_apply.sh`
- `scripts/run_api.sh`
- `scripts/run_frontend.sh`
- `scripts/smoke_e2e.sh`
- `scripts/dev_all.sh`

## Smoke E2E (qué valida)

`make smoke` ejecuta:
1. `POST /api/iei/score`
2. `POST /api/leads` (consentimiento `true`)
3. Login admin + `GET /api/admin/leads` (opcional si `SMOKE_REQUIRE_ADMIN=0`)

## Simulación / stress test

```bash
python3 tools/simulate_leads.py --n 500 --seed 42 --out tools/out/sim_results.csv
python3 tools/simulate_leads.py --n 0 --input-json tools/sample_leads.json --out tools/out/sim_sample.csv
```

## Troubleshooting

### `psql` missing

Instala cliente Postgres en host o usa una DB externa y exporta `DB_URL`.

### Puertos en uso

Cambia en `.env`:
- `API_PORT`
- `FRONTEND_PORT`
- `POSTGRES_PORT`

### Error de conexión DB

Verifica `DB_URL`/`DATABASE_URL`.

Ejemplos:

```bash
DB_URL=postgresql+psycopg://postgres:postgres@localhost:5432/iei_mvp
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/iei_mvp
```

### `pytest` o `fastapi` no encontrados

Ejecuta `make venv` para instalar dependencias en `.venv`.
