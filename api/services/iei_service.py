from __future__ import annotations

from dataclasses import asdict
from typing import Any

import iei_engine as engine_module
from sqlalchemy.orm import Session

from api.errors import ApiException
from api.schemas import LeadInputSchema
from api.services.zone_service import ZoneService
from api.utils.validation import normalize_zone_key


def _to_property_features(payload):
    return engine_module.PropertyFeatures(
        zone_key=normalize_zone_key(payload.zone_key),
        municipality=payload.municipality,
        neighborhood=payload.neighborhood,
        postal_code=payload.postal_code,
        property_type=engine_module.PropertyType(payload.property_type),
        m2=float(payload.m2),
        condition=engine_module.PropertyCondition(payload.condition),
        year_built=payload.year_built,
        has_elevator=payload.has_elevator,
        has_terrace=payload.has_terrace,
        terrace_m2=payload.terrace_m2,
        has_parking=payload.has_parking,
        has_views=payload.has_views,
    )


def _to_owner_signals(payload):
    return engine_module.OwnerSignals(
        sale_horizon=engine_module.SaleHorizon(payload.sale_horizon),
        motivation=engine_module.Motivation(payload.motivation),
        already_listed=engine_module.ListingStatus(payload.already_listed),
        exclusivity=engine_module.ExclusivityDisposition(payload.exclusivity),
        expected_price=payload.expected_price,
    )


def build_lead_input(payload: LeadInputSchema) -> engine_module.LeadInput:
    return engine_module.LeadInput(
        property=_to_property_features(payload.property),
        owner=_to_owner_signals(payload.owner),
    )


def _serialize_result(result: engine_module.IEIResult) -> dict[str, Any]:
    data = asdict(result)
    data["tier"] = result.tier.value
    data["price_estimate"]["demand_level"] = result.price_estimate.demand_level.value

    estimated_range = data["pricing_alignment"].get("estimated_range")
    if isinstance(estimated_range, tuple):
        data["pricing_alignment"]["estimated_range"] = list(estimated_range)

    return data


def _serialize_lead_card(card: dict[str, Any]) -> dict[str, Any]:
    data = dict(card)
    pricing = dict(data.get("pricing", {}))
    estimated = pricing.get("estimated_range")
    if isinstance(estimated, tuple):
        pricing["estimated_range"] = list(estimated)
    data["pricing"] = pricing
    return data


def score_lead(db: Session, payload: LeadInputSchema) -> tuple[engine_module.LeadInput, engine_module.IEIResult, dict[str, Any]]:
    lead = build_lead_input(payload)
    zone_key = normalize_zone_key(lead.property.zone_key)

    ZoneService.assert_zone_configured(db, zone_key)
    ZoneService.apply_runtime_engine_zone_tables(db)

    try:
        result = engine_module.compute_iei(lead)
    except ValueError as exc:
        message = str(exc)
        if "Zona no configurada" in message:
            raise ApiException(
                status_code=422,
                code="ZONE_NOT_CONFIGURED",
                message=message,
                details={"zone_key": zone_key},
            ) from exc
        raise

    serialized = _serialize_result(result)
    return lead, result, serialized


def build_lead_card(lead: engine_module.LeadInput, result: engine_module.IEIResult) -> dict[str, Any]:
    card = engine_module.lead_card(lead, result)
    return _serialize_lead_card(card)
