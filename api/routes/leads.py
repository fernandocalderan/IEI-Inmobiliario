from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.errors import ApiException
from api.schemas import LeadCreateRequestSchema, LeadCreateResponseSchema, LeadDuplicateResponseSchema
from api.services.lead_service import LeadService
from api.utils.ip_hash import request_ip_hash
from api.utils.validation import validate_lead_input

router = APIRouter(prefix="/api", tags=["leads"])


@router.post(
    "/leads",
    response_model=LeadCreateResponseSchema | LeadDuplicateResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_lead(
    payload: LeadCreateRequestSchema,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    if payload.company_website and payload.company_website.strip():
        raise ApiException(
            status_code=400,
            code="BOT_DETECTED",
            message="Se detecto comportamiento automatizado.",
            details={"field": "company_website"},
        )

    validate_lead_input(payload.input)
    ip_hash = request_ip_hash(request)
    result = LeadService.create_lead(db, payload, ip_hash=ip_hash)
    if result.get("duplicate") is True:
        response.status_code = status.HTTP_200_OK
    return result
