import os
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_api_contracts.db")
os.environ.setdefault("USE_DB_ZONES", "false")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin")
os.environ.setdefault("SESSION_SECRET", "test-secret")
os.environ.setdefault("PHONE_HASH_SALT", "test-phone-salt")
os.environ.setdefault("DEDUPE_WINDOW_DAYS", "30")
os.environ.setdefault("FEATURE_RESERVATIONS", "true")

from fastapi.testclient import TestClient

from api.db import Base, SessionLocal, engine
from api.main import app
from api.models import Agency

client = TestClient(app)

AGENCY_1 = "00000000-0000-0000-0000-000000000201"
AGENCY_2 = "00000000-0000-0000-0000-000000000202"


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add(
            Agency(
                id=AGENCY_1,
                name="Agencia Uno",
                email="uno@example.com",
                phone="+34930000111",
                municipality_focus="castelldefels",
                is_active=True,
            )
        )
        db.add(
            Agency(
                id=AGENCY_2,
                name="Agencia Dos",
                email="dos@example.com",
                phone="+34930000112",
                municipality_focus="castelldefels",
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def admin_login():
    resp = client.post("/api/admin/login", json={"password": "test-admin"})
    assert resp.status_code == 200


def base_score_payload(expected_price=None):
    return {
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
            "motivation": "traslado",
            "already_listed": "no",
            "exclusivity": "si",
            "expected_price": expected_price,
        },
    }


def build_lead_payload(phone: str, expected_price=None, honeypot=None):
    payload = {
        "lead": {
            "owner_name": "Lead Test",
            "owner_email": f"{phone[-4:]}@example.com",
            "owner_phone": phone,
            "consent_contact": True,
            "consent_text_version": "v1",
            "source_campaign": "tests",
            "utm_source": "tests",
            "utm_medium": "qa",
            "utm_campaign": "commercial",
            "utm_term": "tier_a",
            "utm_content": "case",
        },
        "input": base_score_payload(expected_price=expected_price),
    }
    if honeypot is not None:
        payload["company_website"] = honeypot
    return payload


def create_tier_a_lead(phone: str) -> str:
    score_resp = client.post("/api/iei/score", json=base_score_payload(expected_price=None))
    assert score_resp.status_code == 200
    adjusted = score_resp.json()["price_estimate"]["adjusted_price"]

    payload = build_lead_payload(phone=phone, expected_price=adjusted)
    resp = client.post("/api/leads", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["result"]["tier"] == "A"
    return data["lead_id"]


def create_non_reserved_sellable_lead(phone: str) -> str:
    payload = build_lead_payload(phone=phone, expected_price=378000)
    resp = client.post("/api/leads", json=payload)
    assert resp.status_code == 201
    return resp.json()["lead_id"]


def test_reserve_and_sell_same_agency_success():
    admin_login()
    lead_id = create_tier_a_lead(phone=f"+34666{uuid4().int % 100000:05d}")

    reserve = client.post(f"/api/admin/leads/{lead_id}/reserve", json={"agency_id": AGENCY_1, "hours": 72})
    assert reserve.status_code == 200
    assert reserve.json()["status"] == "active"

    sell = client.post(f"/api/admin/leads/{lead_id}/sell", json={"agency_id": AGENCY_1, "price_eur": 55})
    assert sell.status_code == 200
    body = sell.json()
    assert body["agency_id"] == AGENCY_1
    assert body["price_eur"] == 55


def test_reserved_by_agency1_sell_by_agency2_returns_409():
    admin_login()
    lead_id = create_tier_a_lead(phone=f"+34666{uuid4().int % 100000:05d}")

    reserve = client.post(f"/api/admin/leads/{lead_id}/reserve", json={"agency_id": AGENCY_1})
    assert reserve.status_code == 200

    sell = client.post(f"/api/admin/leads/{lead_id}/sell", json={"agency_id": AGENCY_2, "price_eur": 60})
    assert sell.status_code == 409
    assert sell.json()["error"]["code"] == "RESERVED_FOR_OTHER"


def test_sell_without_reservation_allowed():
    admin_login()
    lead_id = create_non_reserved_sellable_lead(phone=f"+34666{uuid4().int % 100000:05d}")

    sell = client.post(f"/api/admin/leads/{lead_id}/sell", json={"agency_id": AGENCY_1, "price_eur": 40})
    assert sell.status_code == 200
    assert sell.json()["lead_id"] == lead_id


def test_sell_twice_returns_409():
    admin_login()
    lead_id = create_non_reserved_sellable_lead(phone=f"+34666{uuid4().int % 100000:05d}")

    first = client.post(f"/api/admin/leads/{lead_id}/sell", json={"agency_id": AGENCY_1, "price_eur": 42})
    assert first.status_code == 200

    second = client.post(f"/api/admin/leads/{lead_id}/sell", json={"agency_id": AGENCY_1, "price_eur": 42})
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "SOLD"


def test_dedupe_same_phone_zone_returns_duplicate_true():
    phone = f"+34666{uuid4().int % 100000:05d}"

    first = client.post("/api/leads", json=build_lead_payload(phone=phone, expected_price=378000))
    assert first.status_code == 201
    lead_id = first.json()["lead_id"]

    second = client.post("/api/leads", json=build_lead_payload(phone=phone, expected_price=378000))
    assert second.status_code == 200
    body = second.json()
    assert body["duplicate"] is True
    assert body["existing_lead_id"] == lead_id


def test_honeypot_returns_400():
    payload = build_lead_payload(
        phone=f"+34666{uuid4().int % 100000:05d}",
        expected_price=378000,
        honeypot="https://spam.example",
    )
    resp = client.post("/api/leads", json=payload)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "BOT_DETECTED"


def test_sales_export_csv_works():
    admin_login()
    lead_id = create_non_reserved_sellable_lead(phone=f"+34666{uuid4().int % 100000:05d}")
    sold = client.post(f"/api/admin/leads/{lead_id}/sell", json={"agency_id": AGENCY_1, "price_eur": 35})
    assert sold.status_code == 200

    export_resp = client.get("/api/admin/sales/export.csv")
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers.get("content-type", "")
    body = export_resp.text
    assert "sold_at,lead_id,agency_id,agency_name,zone_key,tier,segment,pricing_policy,lead_price_eur,price_eur,iei_score,iei_framework_version,powered_by,owner_phone_masked,owner_email_masked" in body
    assert lead_id in body
