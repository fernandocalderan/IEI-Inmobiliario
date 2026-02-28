from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db import get_db
from api.schemas import ZonePatchRequestSchema, ZonePatchResponseSchema, ZonesListResponseSchema
from api.services.auth_service import require_admin
from api.services.zone_service import ZoneService

router = APIRouter(prefix="/api/admin/zones", tags=["admin-zones"])


@router.get("", response_model=ZonesListResponseSchema)
def list_zones(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    items = []
    for zone in ZoneService.list_zones(db):
        items.append(
            {
                "id": zone.id,
                "zone_key": zone.zone_key,
                "municipality": zone.municipality,
                "base_per_m2": zone.base_per_m2,
                "demand_level": zone.demand_level,
                "type_factor_overrides": zone.type_factor_overrides,
                "condition_factor_overrides": zone.condition_factor_overrides,
                "extras_add_overrides": zone.extras_add_overrides,
                "extras_cap_override": zone.extras_cap_override,
                "zone_group": zone.zone_group,
                "pricing_policy": zone.pricing_policy,
                "pricing_json": zone.pricing_json,
                "is_premium": zone.is_premium,
                "is_active": zone.is_active,
            }
        )
    return {"items": items}


@router.patch("/{zone_id}", response_model=ZonePatchResponseSchema)
def patch_zone(
    zone_id: str,
    payload: ZonePatchRequestSchema,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    zone = ZoneService.update_zone(db, zone_id, payload)
    return {
        "zone_key": zone.zone_key,
        "base_per_m2": zone.base_per_m2,
        "demand_level": zone.demand_level,
        "updated_at": zone.updated_at,
    }
