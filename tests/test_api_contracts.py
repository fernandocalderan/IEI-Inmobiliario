import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_api_contracts.db")
os.environ.setdefault("USE_DB_ZONES", "false")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin")
os.environ.setdefault("SESSION_SECRET", "test-secret")

from fastapi.testclient import TestClient

from api.db import Base, SessionLocal, engine
from api.main import app
from api.models import Zone
from iei_engine import _tier_from_score, Tier

client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add(
            Zone(
                id="z-castelldefels",
                zone_key="castelldefels",
                municipality="Castelldefels",
                base_per_m2=3350,
                demand_level="alta",
                zone_group="baix_llobregat",
                pricing_policy="baix_llobregat_premium",
                pricing_json={
                    "A": 90,
                    "B": 55,
                    "C": 25,
                    "D": 0,
                    "A_PLUS": 150,
                    "confidence": {"high": 1.2, "medium": 1.0, "low": 0.8, "unreliable": 0.0},
                },
                is_premium=True,
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def valid_score_payload(zone_key="castelldefels"):
    return {
        "property": {
            "zone_key": zone_key,
            "municipality": "Castelldefels",
            "neighborhood": "Centro",
            "postal_code": "08860",
            "property_type": "piso",
            "m2": 90,
            "condition": "buen_estado",
            "year_built": 1998,
            "has_elevator": True,
            "has_terrace": True,
            "terrace_m2": 8,
            "has_parking": False,
            "has_views": False,
        },
        "owner": {
            "sale_horizon": "3-6m",
            "motivation": "compra_otra",
            "already_listed": "no",
            "exclusivity": "depende",
            "expected_price": 380000,
        },
    }


def valid_lead_payload(consent=True):
    return {
        "lead": {
            "owner_name": "Test Owner",
            "owner_email": "owner@example.com",
            "owner_phone": "+34600111222",
            "consent_contact": consent,
            "consent_text_version": "v1",
            "source_campaign": "test_campaign",
            "utm_source": "test",
            "utm_medium": "cpc",
            "utm_campaign": "iei",
            "utm_term": "term",
            "utm_content": "content",
        },
        "input": valid_score_payload(),
    }


def test_score_200_with_valid_payload():
    resp = client.post("/api/iei/score", json=valid_score_payload())
    assert resp.status_code == 200
    data = resp.json()
    assert "iei_score" in data
    assert "tier" in data
    assert "price_estimate" in data
    assert "pricing" in data
    assert "lead_price_eur" in data["pricing"]
    assert "segment" in data["pricing"]
    assert "policy" in data["pricing"]
    assert "iei_framework" in data
    assert data["iei_framework"]["name"] == "IEI™"
    assert data["iei_framework"]["version"] == "1.0"


def test_leads_400_if_consent_false():
    resp = client.post("/api/leads", json=valid_lead_payload(consent=False))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CONSENT_REQUIRED"


def test_score_422_zone_not_configured():
    resp = client.post("/api/iei/score", json=valid_score_payload(zone_key="zona_inexistente"))
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "ZONE_NOT_CONFIGURED"


def test_tier_thresholds_boundaries():
    assert _tier_from_score(85) == Tier.A
    assert _tier_from_score(70) == Tier.B
    assert _tier_from_score(55) == Tier.C
    assert _tier_from_score(54) == Tier.D


def test_lead_201_contains_pricing_and_admin_list_exposes_fields():
    payload = valid_lead_payload(consent=True)
    score_resp = client.post("/api/iei/score", json=payload["input"])
    assert score_resp.status_code == 200
    adjusted = score_resp.json()["price_estimate"]["adjusted_price"]
    payload["input"]["owner"]["expected_price"] = adjusted

    lead_resp = client.post("/api/leads", json=payload)
    assert lead_resp.status_code == 201
    lead_data = lead_resp.json()
    assert "pricing" in lead_data
    assert "lead_price_eur" in lead_data["pricing"]
    assert "segment" in lead_data["pricing"]
    assert "policy" in lead_data["pricing"]
    assert "iei_framework" in lead_data
    assert lead_data["iei_framework"]["version"] == "1.0"
    assert "iei_framework" in lead_data["lead_card"]
    assert lead_data["lead_card"]["powered_by"] == "Powered by IEI™"

    login_resp = client.post("/api/admin/login", json={"password": "test-admin"})
    assert login_resp.status_code == 200

    list_resp = client.get("/api/admin/leads?page=1&page_size=10")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) >= 1
    row = items[0]
    assert "lead_price_eur" in row
    assert "segment" in row
    assert "pricing_policy" in row
    assert "is_premium_zone" in row
