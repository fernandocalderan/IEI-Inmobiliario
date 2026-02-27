from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from api.db import get_db
from api.schemas import (
    AdminLeadListResponseSchema,
    AgenciesListResponseSchema,
    ReleaseReservationRequestSchema,
    ReleaseReservationResponseSchema,
    ReserveLeadRequestSchema,
    ReserveLeadResponseSchema,
    SellLeadRequestSchema,
    SellLeadResponseSchema,
    UpdateLeadStatusRequestSchema,
    UpdateLeadStatusResponseSchema,
)
from api.services.auth_service import require_admin
from api.services.commercial_service import CommercialService
from api.services.lead_service import LeadService

router = APIRouter(prefix="/api/admin", tags=["admin-leads"])


def parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return None


@router.get("/leads", response_model=AdminLeadListResponseSchema)
def list_leads(
    tier: str | None = None,
    zone_key: str | None = None,
    sale_horizon: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return LeadService.list_leads(
        db,
        tier=tier,
        zone_key=zone_key,
        sale_horizon=sale_horizon,
        status=status,
        date_from=parse_optional_datetime(date_from),
        date_to=parse_optional_datetime(date_to),
        page=page,
        page_size=page_size,
    )


@router.get("/leads/{lead_id}")
def lead_detail(
    lead_id: str,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return LeadService.get_lead_detail(db, lead_id)


@router.patch("/leads/{lead_id}", response_model=UpdateLeadStatusResponseSchema)
def patch_lead_status(
    lead_id: str,
    payload: UpdateLeadStatusRequestSchema,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return LeadService.update_status(db, lead_id, payload.status)


@router.post("/leads/{lead_id}/reserve", response_model=ReserveLeadResponseSchema)
def reserve_lead(
    lead_id: str,
    payload: ReserveLeadRequestSchema,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return CommercialService.reserve_lead(db, lead_id, payload.agency_id, payload.hours)


@router.post("/leads/{lead_id}/release-reservation", response_model=ReleaseReservationResponseSchema)
def release_reservation(
    lead_id: str,
    payload: ReleaseReservationRequestSchema,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    _ = payload.reason
    return CommercialService.release_reservation(db, lead_id)


@router.post("/leads/{lead_id}/sell", response_model=SellLeadResponseSchema)
def sell_lead(
    lead_id: str,
    payload: SellLeadRequestSchema,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return CommercialService.sell_lead(db, lead_id, payload.agency_id, payload.price_eur, payload.notes)


@router.get("/sales/export.csv")
def export_sales_csv(
    date_from: str | None = None,
    date_to: str | None = None,
    zone_key: str | None = None,
    agency_id: str | None = None,
    tier: str | None = None,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    csv_text = CommercialService.export_sales_csv(
        db,
        date_from=parse_optional_datetime(date_from),
        date_to=parse_optional_datetime(date_to),
        zone_key=zone_key,
        agency_id=agency_id,
        tier=tier,
    )
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=sales_export.csv"},
    )


@router.get("/agencies", response_model=AgenciesListResponseSchema)
def list_agencies(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    items = []
    for agency in CommercialService.list_agencies(db):
        items.append(
            {
                "id": agency.id,
                "name": agency.name,
                "email": agency.email,
                "phone": agency.phone,
                "municipality_focus": agency.municipality_focus,
                "is_active": agency.is_active,
            }
        )
    return {"items": items}
