from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db import get_db
from api.models import PrivacyDeleteRequest
from api.schemas import PrivacyDeleteRequestSchema, PrivacyDeleteResponseSchema

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.post("/delete-request", response_model=PrivacyDeleteResponseSchema)
def create_delete_request(payload: PrivacyDeleteRequestSchema, db: Session = Depends(get_db)):
    req_id = str(uuid4())
    row = PrivacyDeleteRequest(
        id=req_id,
        email=payload.email,
        phone=payload.phone,
        request_text=payload.request_text,
        status="nuevo",
    )

    db.add(row)
    db.commit()

    return {"ok": True, "request_id": req_id}
