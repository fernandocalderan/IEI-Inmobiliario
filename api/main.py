from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.db import Base, SessionLocal, engine
from api.errors import register_exception_handlers
from api.middleware.rate_limit import SimpleRateLimitMiddleware
from api.middleware.request_id import RequestIDMiddleware
from api.routes import admin_auth, admin_leads, admin_zones, events, iei, leads, privacy
from api.services.zone_service import ZoneService
from api.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SimpleRateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(iei.router)
app.include_router(leads.router)
app.include_router(admin_auth.router)
app.include_router(admin_leads.router)
app.include_router(admin_zones.router)
app.include_router(events.router)
app.include_router(privacy.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ZoneService.ensure_default_zones(db)
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
