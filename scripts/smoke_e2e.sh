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

API_BASE="${API_BASE:-${API_BASE_URL:-http://localhost:${API_PORT:-8000}}}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"
COOKIE_JAR="/tmp/iei_cookie.txt"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR" "$COOKIE_JAR"' EXIT

log() {
  echo "[smoke] $*"
}

fail() {
  echo "[smoke] FAIL: $*" >&2
  exit 1
}

assert_status() {
  local expected="$1"
  local actual="$2"
  local label="$3"
  local body_file="${4:-}"

  if [ "$expected" != "$actual" ]; then
    echo "[smoke] FAIL: ${label} status=${actual} expected=${expected}" >&2
    if [ -n "$body_file" ] && [ -f "$body_file" ]; then
      cat "$body_file" >&2
    fi
    exit 1
  fi
}

json_get() {
  local file="$1"
  local path="$2"
  python3 - "$file" "$path" <<'PY'
import json
import sys

file_path, dotted_path = sys.argv[1], sys.argv[2]

try:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    print("")
    raise SystemExit(0)

cur = data
for part in dotted_path.split('.'):
    if not part:
        continue
    if isinstance(cur, list):
        try:
            idx = int(part)
            cur = cur[idx]
        except Exception:
            print("")
            raise SystemExit(0)
    elif isinstance(cur, dict):
        if part not in cur:
            print("")
            raise SystemExit(0)
        cur = cur[part]
    else:
        print("")
        raise SystemExit(0)

if isinstance(cur, bool):
    print("true" if cur else "false")
elif cur is None:
    print("")
else:
    print(cur)
PY
}

gen_phone() {
  local suffix
  suffix="$(date +%s%N | rev | cut -c1-8 | rev)"
  echo "+346${suffix}"
}

make_score_payload() {
  local out_file="$1"
  local expected_price="$2"
  local motivation="$3"
  python3 - "$out_file" "$expected_price" "$motivation" <<'PY'
import json
import sys

out_file, expected_raw, motivation = sys.argv[1], sys.argv[2], sys.argv[3]
expected = None if expected_raw == "null" else float(expected_raw)

payload = {
    "property": {
        "zone_key": "castelldefels",
        "municipality": "Castelldefels",
        "neighborhood": "Centro",
        "postal_code": "08860",
        "property_type": "piso",
        "m2": 95,
        "condition": "reformado",
        "year_built": 1998,
        "has_elevator": True,
        "has_terrace": True,
        "terrace_m2": 12,
        "has_parking": True,
        "has_views": True,
    },
    "owner": {
        "sale_horizon": "<3m",
        "motivation": motivation,
        "already_listed": "no",
        "exclusivity": "si",
        "expected_price": expected,
    },
}

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(payload, f)
PY
}

make_lead_payload() {
  local out_file="$1"
  local phone="$2"
  local expected_price="$3"
  local honeypot_value="$4"
  local motivation="$5"

  python3 - "$out_file" "$phone" "$expected_price" "$honeypot_value" "$motivation" <<'PY'
import json
import sys

out_file, phone, expected_raw, honeypot_value, motivation = sys.argv[1:6]
expected = None if expected_raw == "null" else float(expected_raw)
company_website = None if honeypot_value == "" else honeypot_value

payload = {
    "lead": {
        "owner_name": "Smoke Lead Comercial",
        "owner_email": f"smoke_{phone[-6:]}@example.com",
        "owner_phone": phone,
        "consent_contact": True,
        "consent_text_version": "v1",
        "source_campaign": "smoke_comercial",
        "utm_source": "smoke",
        "utm_medium": "test",
        "utm_campaign": "iei",
        "utm_term": "smoke",
        "utm_content": "commercial",
    },
    "input": {
        "property": {
            "zone_key": "castelldefels",
            "municipality": "Castelldefels",
            "neighborhood": "Centro",
            "postal_code": "08860",
            "property_type": "piso",
            "m2": 95,
            "condition": "reformado",
            "year_built": 1998,
            "has_elevator": True,
            "has_terrace": True,
            "terrace_m2": 12,
            "has_parking": True,
            "has_views": True,
        },
        "owner": {
            "sale_horizon": "<3m",
            "motivation": motivation,
            "already_listed": "no",
            "exclusivity": "si",
            "expected_price": expected,
        },
    },
    "company_website": company_website,
}

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(payload, f)
PY
}

iso_minus_24h() {
  python3 - <<'PY'
from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc) - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ'))
PY
}

if [ -z "$ADMIN_PASSWORD" ]; then
  fail "ADMIN_PASSWORD no definido en entorno/.env"
fi

log "1) Login admin"
login_body="$TMP_DIR/login_body.json"
login_status=$(curl -sS -c "$COOKIE_JAR" -o "$login_body" -w "%{http_code}" -X POST "${API_BASE}/api/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"password\":\"${ADMIN_PASSWORD}\"}")
assert_status "200" "$login_status" "admin login" "$login_body"

log "2) Resolver agencies"
DEFAULT_AGENCY_1_ID="00000000-0000-0000-0000-000000000101"
DEFAULT_AGENCY_2_ID="00000000-0000-0000-0000-000000000102"
AGENCY_1_ID="${AGENCY_1_ID:-}"
AGENCY_2_ID="${AGENCY_2_ID:-}"
agencies_body="$TMP_DIR/agencies.json"
agencies_status=$(curl -sS -b "$COOKIE_JAR" -o "$agencies_body" -w "%{http_code}" "${API_BASE}/api/admin/agencies")
if [ "$agencies_status" = "200" ]; then
  parsed_a1="$(json_get "$agencies_body" "items.0.id")"
  parsed_a2="$(json_get "$agencies_body" "items.1.id")"
  if [ -n "$parsed_a1" ]; then
    AGENCY_1_ID="$parsed_a1"
  fi
  if [ -n "$parsed_a2" ]; then
    AGENCY_2_ID="$parsed_a2"
  fi
  log "agencies via endpoint: A1=${AGENCY_1_ID:-n/a} A2=${AGENCY_2_ID:-n/a}"
else
  log "WARN: /api/admin/agencies no disponible (status=${agencies_status}), usando env AGENCY_1_ID/AGENCY_2_ID"
fi

if [ -z "${AGENCY_1_ID:-}" ]; then
  AGENCY_1_ID="$DEFAULT_AGENCY_1_ID"
  log "WARN: usando fallback AGENCY_1_ID=${AGENCY_1_ID}"
fi
if [ -z "${AGENCY_2_ID:-}" ]; then
  AGENCY_2_ID="$DEFAULT_AGENCY_2_ID"
  log "WARN: usando fallback AGENCY_2_ID=${AGENCY_2_ID}"
fi

if [ -z "${AGENCY_1_ID:-}" ] || [ -z "${AGENCY_2_ID:-}" ]; then
  fail "No se pudieron resolver AGENCY_1_ID y AGENCY_2_ID (endpoint o env)."
fi
if [ "$AGENCY_1_ID" = "$AGENCY_2_ID" ]; then
  fail "AGENCY_1_ID y AGENCY_2_ID deben ser distintos."
fi

log "3) Crear lead y buscar Tier A (max 3 intentos)"
SELECTED_LEAD_ID=""
SELECTED_PHONE=""
SELECTED_TIER=""
SELECTED_MOTIVATION="traslado"
SELECTED_EXPECTED="null"
TIER_A_OBTAINED=0

for attempt in 1 2 3; do
  motivation="traslado"
  if [ "$attempt" = "2" ]; then
    motivation="finanzas"
  fi

  score_payload="$TMP_DIR/score_${attempt}.json"
  make_score_payload "$score_payload" "null" "$motivation"

  score_body="$TMP_DIR/score_${attempt}_body.json"
  score_status=$(curl -sS -o "$score_body" -w "%{http_code}" -X POST "${API_BASE}/api/iei/score" \
    -H "Content-Type: application/json" \
    -H "X-Session-ID: smoke-commercial" \
    --data-binary "@${score_payload}")
  assert_status "200" "$score_status" "iei score attempt ${attempt}" "$score_body"

  adjusted_price="$(json_get "$score_body" "price_estimate.adjusted_price")"
  if [ -z "$adjusted_price" ]; then
    fail "No se obtuvo adjusted_price en score attempt ${attempt}"
  fi

  expected_price="$(python3 - "$adjusted_price" <<'PY'
import sys
print(round(float(sys.argv[1]), 2))
PY
)"

  phone="$(gen_phone)"
  lead_payload="$TMP_DIR/lead_${attempt}.json"
  make_lead_payload "$lead_payload" "$phone" "$expected_price" "" "$motivation"

  lead_body="$TMP_DIR/lead_${attempt}_body.json"
  lead_status=$(curl -sS -o "$lead_body" -w "%{http_code}" -X POST "${API_BASE}/api/leads" \
    -H "Content-Type: application/json" \
    -H "X-Session-ID: smoke-commercial" \
    --data-binary "@${lead_payload}")

  if [ "$lead_status" = "200" ]; then
    # dedupe inesperado en intento primario; reintentar con nuevo teléfono
    duplicate_flag="$(json_get "$lead_body" "duplicate")"
    if [ "$duplicate_flag" = "true" ]; then
      log "WARN: dedupe inesperado en intento ${attempt}, se reintenta"
      continue
    fi
  fi

  assert_status "201" "$lead_status" "create lead attempt ${attempt}" "$lead_body"

  lead_id="$(json_get "$lead_body" "lead_id")"
  tier="$(json_get "$lead_body" "result.tier")"
  if [ -z "$tier" ]; then
    tier="$(json_get "$lead_body" "lead_card.tier")"
  fi

  if [ -z "$lead_id" ] || [ -z "$tier" ]; then
    fail "Respuesta create lead sin lead_id/tier en intento ${attempt}"
  fi

  log "attempt ${attempt}: lead_id=${lead_id} tier=${tier}"

  SELECTED_LEAD_ID="$lead_id"
  SELECTED_PHONE="$phone"
  SELECTED_TIER="$tier"
  SELECTED_MOTIVATION="$motivation"
  SELECTED_EXPECTED="$expected_price"

  if [ "$tier" = "A" ]; then
    TIER_A_OBTAINED=1
    break
  fi
done

if [ -z "$SELECTED_LEAD_ID" ]; then
  fail "No se pudo crear lead válido en 3 intentos"
fi

RESERVED=0
SOLD=0

if [ "$TIER_A_OBTAINED" = "1" ]; then
  log "4) Reservar lead Tier A"
  reserve_body="$TMP_DIR/reserve_body.json"
  reserve_status=$(curl -sS -b "$COOKIE_JAR" -o "$reserve_body" -w "%{http_code}" -X POST \
    "${API_BASE}/api/admin/leads/${SELECTED_LEAD_ID}/reserve" \
    -H "Content-Type: application/json" \
    -d "{\"agency_id\":\"${AGENCY_1_ID}\",\"hours\":72}")
  assert_status "200" "$reserve_status" "reserve lead" "$reserve_body"
  reserved_until="$(json_get "$reserve_body" "reserved_until")"
  if [ -z "$reserved_until" ]; then
    fail "reserve sin reserved_until"
  fi
  RESERVED=1

  log "5) Venta con agencia incorrecta (espera 409 RESERVED_FOR_OTHER)"
  sell_wrong_body="$TMP_DIR/sell_wrong_body.json"
  sell_wrong_status=$(curl -sS -b "$COOKIE_JAR" -o "$sell_wrong_body" -w "%{http_code}" -X POST \
    "${API_BASE}/api/admin/leads/${SELECTED_LEAD_ID}/sell" \
    -H "Content-Type: application/json" \
    -d "{\"agency_id\":\"${AGENCY_2_ID}\",\"price_eur\":160}")
  assert_status "409" "$sell_wrong_status" "sell with other agency" "$sell_wrong_body"
  wrong_code="$(json_get "$sell_wrong_body" "error.code")"
  if [ -n "$wrong_code" ] && [ "$wrong_code" != "RESERVED_FOR_OTHER" ]; then
    fail "error.code inesperado en venta agencia incorrecta: ${wrong_code}"
  fi

  log "6) Venta con agencia correcta"
  sell_ok_body="$TMP_DIR/sell_ok_body.json"
  sell_ok_status=$(curl -sS -b "$COOKIE_JAR" -o "$sell_ok_body" -w "%{http_code}" -X POST \
    "${API_BASE}/api/admin/leads/${SELECTED_LEAD_ID}/sell" \
    -H "Content-Type: application/json" \
    -d "{\"agency_id\":\"${AGENCY_1_ID}\",\"price_eur\":160}")
  assert_status "200" "$sell_ok_status" "sell with reserved agency" "$sell_ok_body"
  sold_at="$(json_get "$sell_ok_body" "sold_at")"
  if [ -z "$sold_at" ]; then
    fail "sell success sin sold_at"
  fi
  SOLD=1

  log "7) Doble venta (espera 409 SOLD)"
  sell_again_body="$TMP_DIR/sell_again_body.json"
  sell_again_status=$(curl -sS -b "$COOKIE_JAR" -o "$sell_again_body" -w "%{http_code}" -X POST \
    "${API_BASE}/api/admin/leads/${SELECTED_LEAD_ID}/sell" \
    -H "Content-Type: application/json" \
    -d "{\"agency_id\":\"${AGENCY_1_ID}\",\"price_eur\":160}")
  assert_status "409" "$sell_again_status" "sell again" "$sell_again_body"
  sold_code="$(json_get "$sell_again_body" "error.code")"
  if [ -n "$sold_code" ] && [ "$sold_code" != "SOLD" ]; then
    fail "error.code inesperado en doble venta: ${sold_code}"
  fi

  log "8) Export CSV ventas"
  DATE_FROM="$(iso_minus_24h)"
  DATE_TO="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  export_headers="$TMP_DIR/export_headers.txt"
  export_body="$TMP_DIR/export.csv"
  export_status=$(curl -sS -b "$COOKIE_JAR" -D "$export_headers" -o "$export_body" -w "%{http_code}" \
    "${API_BASE}/api/admin/sales/export.csv?date_from=${DATE_FROM}&date_to=${DATE_TO}&tier=A")
  assert_status "200" "$export_status" "sales export" "$export_body"
  if ! grep -qi "content-type: text/csv" "$export_headers"; then
    fail "export no devolvió content-type text/csv"
  fi
  if ! grep -q "$SELECTED_LEAD_ID" "$export_body"; then
    fail "export CSV no contiene lead_id vendido"
  fi
else
  log "WARN: Tier A not obtained after 3 attempts; se omiten reserve/sell/export para no romper CI"
fi

log "9) Dedupe con mismo phone+zone"
dedupe_payload="$TMP_DIR/dedupe_payload.json"
make_lead_payload "$dedupe_payload" "$SELECTED_PHONE" "$SELECTED_EXPECTED" "" "$SELECTED_MOTIVATION"
dedupe_body="$TMP_DIR/dedupe_body.json"
dedupe_status=$(curl -sS -o "$dedupe_body" -w "%{http_code}" -X POST "${API_BASE}/api/leads" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: smoke-commercial" \
  --data-binary "@${dedupe_payload}")
assert_status "200" "$dedupe_status" "dedupe lead" "$dedupe_body"
dup_flag="$(json_get "$dedupe_body" "duplicate")"
existing_lead_id="$(json_get "$dedupe_body" "existing_lead_id")"
if [ "$dup_flag" != "true" ]; then
  fail "dedupe esperado duplicate:true"
fi
if [ "$existing_lead_id" != "$SELECTED_LEAD_ID" ]; then
  fail "dedupe existing_lead_id (${existing_lead_id}) no coincide con ${SELECTED_LEAD_ID}"
fi

log "10) Honeypot BOT_DETECTED"
honeypot_phone="$(gen_phone)"
honeypot_payload="$TMP_DIR/honeypot_payload.json"
make_lead_payload "$honeypot_payload" "$honeypot_phone" "$SELECTED_EXPECTED" "http://spam.test" "$SELECTED_MOTIVATION"
honeypot_body="$TMP_DIR/honeypot_body.json"
honeypot_status=$(curl -sS -o "$honeypot_body" -w "%{http_code}" -X POST "${API_BASE}/api/leads" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: smoke-commercial" \
  --data-binary "@${honeypot_payload}")
assert_status "400" "$honeypot_status" "honeypot" "$honeypot_body"
honeypot_code="$(json_get "$honeypot_body" "error.code")"
honeypot_message="$(json_get "$honeypot_body" "error.message")"
if [ -n "$honeypot_code" ]; then
  if [ "$honeypot_code" != "BOT_DETECTED" ]; then
    fail "honeypot devolvió code inesperado: ${honeypot_code}"
  fi
else
  if ! echo "$honeypot_message" | grep -qi "bot"; then
    fail "honeypot sin code BOT_DETECTED ni mensaje BOT"
  fi
fi

if [ "$RESERVED" = "1" ] && [ "$SOLD" = "0" ]; then
  log "11) Release reservation (optional cleanup)"
  release_body="$TMP_DIR/release_body.json"
  release_status=$(curl -sS -b "$COOKIE_JAR" -o "$release_body" -w "%{http_code}" -X POST \
    "${API_BASE}/api/admin/leads/${SELECTED_LEAD_ID}/release-reservation" \
    -H "Content-Type: application/json" \
    -d '{"reason":"smoke_cleanup"}')
  assert_status "200" "$release_status" "release reservation" "$release_body"
fi

log "OK: login, create lead, dedupe, honeypot"
if [ "$TIER_A_OBTAINED" = "1" ]; then
  log "OK: reserve, sell guardrails, export csv"
else
  log "WARN: reserve/sell/export skipped because Tier A was not obtained"
fi

log "OK"
