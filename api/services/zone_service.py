from __future__ import annotations

import threading
import time
from uuid import uuid4

import iei_engine as engine_module
from sqlalchemy.orm import Session

from api.errors import ApiException
from api.models import Zone
from api.schemas import ZonePatchRequestSchema
from api.settings import get_settings


class ZoneService:
    _lock = threading.RLock()
    _cache_expire_at = 0.0

    @staticmethod
    def normalize_zone_key(zone_key: str) -> str:
        return zone_key.lower().strip()

    @staticmethod
    def list_zones(db: Session) -> list[Zone]:
        return db.query(Zone).order_by(Zone.zone_key.asc()).all()

    @staticmethod
    def get_zone_by_id(db: Session, zone_id: str) -> Zone | None:
        return db.query(Zone).filter(Zone.id == zone_id).first()

    @staticmethod
    def ensure_default_zones(db: Session) -> None:
        existing = {z.zone_key for z in db.query(Zone).all()}
        now_rows = []
        if "castelldefels" not in existing:
            now_rows.append(
                Zone(
                    id=str(uuid4()),
                    zone_key="castelldefels",
                    municipality="Castelldefels",
                    base_per_m2=3350,
                    demand_level="alta",
                    is_active=True,
                )
            )
        if "gava" not in existing:
            now_rows.append(
                Zone(
                    id=str(uuid4()),
                    zone_key="gava",
                    municipality="Gava",
                    base_per_m2=3100,
                    demand_level="media",
                    is_active=True,
                )
            )
        if "sitges" not in existing:
            now_rows.append(
                Zone(
                    id=str(uuid4()),
                    zone_key="sitges",
                    municipality="Sitges",
                    base_per_m2=4100,
                    demand_level="alta",
                    is_active=True,
                )
            )

        if now_rows:
            for row in now_rows:
                db.add(row)
            db.commit()

    @classmethod
    def assert_zone_configured(cls, db: Session, zone_key: str) -> None:
        normalized = cls.normalize_zone_key(zone_key)
        settings = get_settings()

        if settings.use_db_zones:
            zone = (
                db.query(Zone)
                .filter(Zone.zone_key == normalized, Zone.is_active.is_(True))
                .first()
            )
            if not zone:
                raise ApiException(
                    status_code=422,
                    code="ZONE_NOT_CONFIGURED",
                    message=f"Zona no configurada: {normalized}",
                    details={"zone_key": normalized},
                )
        else:
            if normalized not in engine_module.BASE_PRICE_PER_M2:
                raise ApiException(
                    status_code=422,
                    code="ZONE_NOT_CONFIGURED",
                    message=f"Zona no configurada: {normalized}",
                    details={"zone_key": normalized},
                )

    @classmethod
    def apply_runtime_engine_zone_tables(cls, db: Session) -> None:
        settings = get_settings()
        if not settings.use_db_zones:
            return

        now = time.time()

        with cls._lock:
            if now < cls._cache_expire_at:
                return

            active_zones = (
                db.query(Zone)
                .filter(Zone.is_active.is_(True))
                .order_by(Zone.zone_key.asc())
                .all()
            )

            base_map: dict[str, float] = {}
            demand_map: dict[str, engine_module.DemandLevel] = {}

            for row in active_zones:
                zone_key = cls.normalize_zone_key(row.zone_key)
                base_map[zone_key] = float(row.base_per_m2)
                try:
                    demand_map[zone_key] = engine_module.DemandLevel(row.demand_level)
                except ValueError:
                    demand_map[zone_key] = engine_module.DemandLevel.MEDIA

            if base_map:
                engine_module.BASE_PRICE_PER_M2.clear()
                engine_module.BASE_PRICE_PER_M2.update(base_map)

                engine_module.DEMAND_INDEX.clear()
                engine_module.DEMAND_INDEX.update(demand_map)

            cls._cache_expire_at = now + settings.zone_cache_ttl_seconds

    @classmethod
    def invalidate_cache(cls) -> None:
        with cls._lock:
            cls._cache_expire_at = 0

    @classmethod
    def update_zone(cls, db: Session, zone_id: str, payload: ZonePatchRequestSchema) -> Zone:
        zone = cls.get_zone_by_id(db, zone_id)
        if not zone:
            raise ApiException(
                status_code=404,
                code="NOT_FOUND",
                message="Zona no encontrada.",
                details={"zone_id": zone_id},
            )

        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(zone, key, value)

        db.add(zone)
        db.commit()
        db.refresh(zone)

        cls.invalidate_cache()
        return zone
