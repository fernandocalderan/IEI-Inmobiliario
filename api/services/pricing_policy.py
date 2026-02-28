from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy.orm import Session

from api.models import Zone

BAIX_LLOBREGAT_PREMIUM_POLICY = "baix_llobregat_premium"
BAIX_LLOBREGAT_PREMIUM_POLICY_VERSION = "v1"
BAIX_LLOBREGAT_PREMIUM_ZONES = {"castelldefels", "gava", "sitges"}

DEFAULT_PREMIUM_PRICING_JSON = {
    "A": 90,
    "B": 55,
    "C": 25,
    "D": 0,
    "A_PLUS": 150,
    "confidence": {
        "high": 1.2,
        "medium": 1.0,
        "low": 0.8,
        "unreliable": 0.0,
    },
}

DEFAULT_STANDARD_PRICING_JSON = {
    "A": 45,
    "B": 30,
    "C": 15,
    "D": 0,
    "A_PLUS": 70,
    "confidence": {
        "high": 1.2,
        "medium": 1.0,
        "low": 0.8,
        "unreliable": 0.0,
    },
}


@dataclass(frozen=True)
class PricingContext:
    tier: str
    zone_key: str
    sale_horizon: str
    already_listed: str
    gap_percent: float | None
    demand_level: str
    confidence_bucket: str | None = None


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_money(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class PricingPolicyService:
    @staticmethod
    def _zone_row(db: Session, zone_key: str) -> Zone | None:
        return db.query(Zone).filter(Zone.zone_key == zone_key.lower().strip()).first()

    @classmethod
    def _resolve_policy(cls, zone: Zone | None, zone_key: str) -> tuple[str, bool, dict[str, Any]]:
        normalized_zone = zone_key.lower().strip()

        if zone and isinstance(zone.pricing_json, dict) and zone.pricing_json:
            policy_name = zone.pricing_policy or BAIX_LLOBREGAT_PREMIUM_POLICY
            is_premium = bool(zone.is_premium)
            return policy_name, is_premium, dict(zone.pricing_json)

        zone_is_premium = bool(zone.is_premium) if zone else normalized_zone in BAIX_LLOBREGAT_PREMIUM_ZONES
        zone_policy = zone.pricing_policy if zone and zone.pricing_policy else None

        if zone_is_premium or zone_policy == BAIX_LLOBREGAT_PREMIUM_POLICY:
            return BAIX_LLOBREGAT_PREMIUM_POLICY, True, dict(DEFAULT_PREMIUM_PRICING_JSON)

        return zone_policy or "standard_mvp_policy", False, dict(DEFAULT_STANDARD_PRICING_JSON)

    @staticmethod
    def _resolve_confidence_bucket(confidence_bucket: str | None) -> str:
        if not confidence_bucket:
            return "medium"
        normalized = confidence_bucket.lower().strip()
        if normalized in {"high", "medium", "low", "unreliable"}:
            return normalized
        return "medium"

    @classmethod
    def _segment_from_context(cls, context: PricingContext) -> str:
        if context.tier != "A":
            return context.tier

        confidence_ok = True
        if context.confidence_bucket:
            confidence_ok = cls._resolve_confidence_bucket(context.confidence_bucket) == "high"

        if (
            context.sale_horizon == "<3m"
            and context.already_listed == "no"
            and context.demand_level == "alta"
            and context.gap_percent is not None
            and float(context.gap_percent) <= 5.0
            and confidence_ok
        ):
            return "A_PLUS"

        return "A"

    @classmethod
    def compute_pricing(cls, db: Session, context: PricingContext) -> dict[str, Any]:
        zone_key = context.zone_key.lower().strip()
        zone = cls._zone_row(db, zone_key)

        policy_name, is_premium_zone, policy_json = cls._resolve_policy(zone, zone_key)
        confidence_bucket = cls._resolve_confidence_bucket(context.confidence_bucket)
        segment = cls._segment_from_context(context)

        confidence_map = policy_json.get("confidence") if isinstance(policy_json.get("confidence"), dict) else {}
        confidence_multiplier = _as_float(confidence_map.get(confidence_bucket), 1.0)

        base_tier_key = segment if segment == "A_PLUS" else context.tier
        base_price = _as_float(policy_json.get(base_tier_key), 0.0)
        lead_price = 0.0 if confidence_multiplier <= 0 else _to_money(base_price * confidence_multiplier)

        if context.tier == "D":
            lead_price = 0.0
            segment = "D"

        return {
            "lead_price_eur": lead_price,
            "segment": segment,
            "policy": policy_name,
            "policy_version": BAIX_LLOBREGAT_PREMIUM_POLICY_VERSION if policy_name == BAIX_LLOBREGAT_PREMIUM_POLICY else "v1",
            "confidence_bucket": confidence_bucket,
            "is_premium_zone": is_premium_zone,
            "policy_json": policy_json,
        }
