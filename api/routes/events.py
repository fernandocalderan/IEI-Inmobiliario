from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db import get_db
from api.errors import ApiException
from api.models import Event
from api.schemas import EventRequestSchema, EventResponseSchema

router = APIRouter(prefix="/api", tags=["events"])


@router.post("/events", response_model=EventResponseSchema)
def track_event(payload: EventRequestSchema, db: Session = Depends(get_db)):
    if not payload.session_id:
        raise ApiException(
            status_code=400,
            code="VALIDATION_ERROR",
            message="session_id es obligatorio.",
            details={"field": "session_id"},
        )

    if payload.event_name == "submit_lead" and payload.lead_id:
        existing = (
            db.query(Event)
            .filter(Event.event_name == "submit_lead", Event.lead_id == payload.lead_id)
            .first()
        )
        if existing:
            return {"ok": True, "deduplicated": True}

    row = Event(
        id=str(uuid4()),
        event_name=payload.event_name,
        event_version=payload.event_version,
        session_id=payload.session_id,
        lead_id=payload.lead_id,
        payload_json=payload.payload,
    )

    db.add(row)
    db.commit()

    return {"ok": True, "deduplicated": False}
