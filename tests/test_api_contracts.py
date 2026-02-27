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
