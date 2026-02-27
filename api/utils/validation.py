from __future__ import annotations

from api.errors import ApiException
from api.schemas import LeadInputSchema


def normalize_zone_key(value: str) -> str:
    return value.lower().strip()


def validate_lead_input(payload: LeadInputSchema) -> None:
    issues: list[dict[str, str]] = []

    if payload.property.m2 <= 0:
        issues.append({"field": "property.m2", "message": "m2 debe ser > 0"})

    if payload.owner.expected_price is not None and payload.owner.expected_price <= 0:
        issues.append({"field": "owner.expected_price", "message": "expected_price debe ser null o > 0"})

    if issues:
        raise ApiException(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Datos de entrada invalidos.",
            details={"issues": issues},
        )
