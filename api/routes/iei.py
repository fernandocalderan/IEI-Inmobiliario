from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db import get_db
from api.schemas import IEIResultSchema, LeadInputSchema
from api.services.iei_service import compute_pricing_from_result, get_framework_metadata, score_lead
from api.utils.validation import validate_lead_input

router = APIRouter(prefix="/api/iei", tags=["iei"])


@router.post("/score", response_model=IEIResultSchema)
def score(payload: LeadInputSchema, db: Session = Depends(get_db)):
    validate_lead_input(payload)
    _, _, result = score_lead(db, payload)
    pricing = compute_pricing_from_result(db, payload, result)
    result["pricing"] = {
        "lead_price_eur": pricing["lead_price_eur"],
        "segment": pricing["segment"],
        "policy": pricing["policy"],
        "confidence_bucket": pricing["confidence_bucket"],
    }
    framework = get_framework_metadata()
    if framework:
        result["iei_framework"] = framework
    return result
