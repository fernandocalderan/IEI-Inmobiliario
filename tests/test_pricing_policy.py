import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_pricing_policy.db")
os.environ.setdefault("USE_DB_ZONES", "true")

from api.db import Base, SessionLocal, engine
from api.models import Zone
from api.services.pricing_policy import PricingContext, PricingPolicyService


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def test_a_plus_segment_positive():
    db = SessionLocal()
    try:
        result = PricingPolicyService.compute_pricing(
            db,
            PricingContext(
                tier="A",
                zone_key="castelldefels",
                sale_horizon="<3m",
                already_listed="no",
                gap_percent=4.5,
                demand_level="alta",
                confidence_bucket=None,
            ),
        )
        assert result["segment"] == "A_PLUS"
        assert result["lead_price_eur"] == 150.0
    finally:
        db.close()


def test_a_plus_segment_negative_when_gap_high():
    db = SessionLocal()
    try:
        result = PricingPolicyService.compute_pricing(
            db,
            PricingContext(
                tier="A",
                zone_key="castelldefels",
                sale_horizon="<3m",
                already_listed="no",
                gap_percent=12.0,
                demand_level="alta",
                confidence_bucket=None,
            ),
        )
        assert result["segment"] == "A"
        assert result["lead_price_eur"] == 90.0
    finally:
        db.close()


def test_pricing_applied_from_zone_policy_json():
    db = SessionLocal()
    try:
        db.add(
            Zone(
                id="z-policy-1",
                zone_key="custom_zone",
                municipality="Custom",
                base_per_m2=3000,
                demand_level="alta",
                pricing_policy="custom_policy",
                pricing_json={
                    "A": 100,
                    "B": 50,
                    "C": 20,
                    "D": 0,
                    "A_PLUS": 180,
                    "confidence": {"high": 1.0, "medium": 1.0, "low": 1.0, "unreliable": 0.0},
                },
                is_premium=True,
                is_active=True,
            )
        )
        db.commit()

        result = PricingPolicyService.compute_pricing(
            db,
            PricingContext(
                tier="A",
                zone_key="custom_zone",
                sale_horizon="<3m",
                already_listed="no",
                gap_percent=2.0,
                demand_level="alta",
                confidence_bucket=None,
            ),
        )
        assert result["policy"] == "custom_policy"
        assert result["segment"] == "A_PLUS"
        assert result["lead_price_eur"] == 180.0
    finally:
        db.close()


def test_confidence_multiplier_is_applied():
    db = SessionLocal()
    try:
        high = PricingPolicyService.compute_pricing(
            db,
            PricingContext(
                tier="B",
                zone_key="castelldefels",
                sale_horizon="3-6m",
                already_listed="no",
                gap_percent=3.0,
                demand_level="alta",
                confidence_bucket="high",
            ),
        )
        low = PricingPolicyService.compute_pricing(
            db,
            PricingContext(
                tier="B",
                zone_key="castelldefels",
                sale_horizon="3-6m",
                already_listed="no",
                gap_percent=3.0,
                demand_level="alta",
                confidence_bucket="low",
            ),
        )
        unreliable = PricingPolicyService.compute_pricing(
            db,
            PricingContext(
                tier="B",
                zone_key="castelldefels",
                sale_horizon="3-6m",
                already_listed="no",
                gap_percent=3.0,
                demand_level="alta",
                confidence_bucket="unreliable",
            ),
        )
        assert high["lead_price_eur"] == 66.0
        assert low["lead_price_eur"] == 44.0
        assert unreliable["lead_price_eur"] == 0.0
    finally:
        db.close()
