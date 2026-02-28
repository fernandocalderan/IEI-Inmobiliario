from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from io import StringIO
from uuid import uuid4

from sqlalchemy.orm import Session

from api.errors import ApiException
from api.iei_framework import IEI_FRAMEWORK_VERSION, IEI_POWERED_BY
from api.models import Agency, IEIResultRecord, Lead, LeadReservation, LeadSale, PropertyInput
from api.settings import get_settings


def _now() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _mask_phone(phone: str | None, *, export_pii: bool) -> str:
    if not phone:
        return ""
    if export_pii:
        return phone
    clean = phone.strip()
    if len(clean) <= 4:
        return "*" * len(clean)
    return f"{clean[:3]}***{clean[-2:]}"


def _mask_email(email: str | None, *, export_pii: bool) -> str:
    if not email:
        return ""
    if export_pii:
        return email
    local, sep, domain = email.partition("@")
    if not sep:
        return "***"
    if len(local) <= 2:
        return f"{local[:1]}***@{domain}"
    return f"{local[:2]}***@{domain}"


class CommercialService:
    @staticmethod
    def list_agencies(db: Session) -> list[Agency]:
        return (
            db.query(Agency)
            .filter(Agency.is_active.is_(True))
            .order_by(Agency.name.asc())
            .all()
        )

    @staticmethod
    def _get_lead_or_404(db: Session, lead_id: str) -> Lead:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ApiException(
                status_code=404,
                code="NOT_FOUND",
                message="Lead no encontrado.",
                details={"lead_id": lead_id},
            )
        return lead

    @staticmethod
    def _get_active_agency_or_404(db: Session, agency_id: str) -> Agency:
        agency = db.query(Agency).filter(Agency.id == agency_id, Agency.is_active.is_(True)).first()
        if not agency:
            raise ApiException(
                status_code=404,
                code="NOT_FOUND",
                message="Agencia no encontrada o inactiva.",
                details={"agency_id": agency_id},
            )
        return agency

    @staticmethod
    def _lead_tier(db: Session, lead_id: str) -> str | None:
        row = (
            db.query(IEIResultRecord)
            .filter(IEIResultRecord.lead_id == lead_id)
            .order_by(IEIResultRecord.created_at.desc())
            .first()
        )
        return row.tier if row else None

    @staticmethod
    def _sale_for_lead(db: Session, lead_id: str) -> LeadSale | None:
        return db.query(LeadSale).filter(LeadSale.lead_id == lead_id).first()

    @staticmethod
    def _reservation_for_lead(db: Session, lead_id: str) -> LeadReservation | None:
        return db.query(LeadReservation).filter(LeadReservation.lead_id == lead_id).first()

    @classmethod
    def _normalize_reservation_state(cls, db: Session, reservation: LeadReservation | None) -> LeadReservation | None:
        if not reservation:
            return None
        if reservation.status == "active" and _as_utc(reservation.reserved_until) <= _now():
            reservation.status = "expired"
            db.add(reservation)
            db.commit()
            db.refresh(reservation)
        return reservation

    @classmethod
    def get_commercial_state(cls, db: Session, lead_id: str) -> dict:
        sale = cls._sale_for_lead(db, lead_id)
        if sale:
            return {
                "commercial_state": "sold",
                "reserved_until": None,
                "reserved_to_agency_id": None,
                "sold_at": sale.sold_at,
            }

        reservation = cls._normalize_reservation_state(db, cls._reservation_for_lead(db, lead_id))
        if reservation and reservation.status == "active":
            return {
                "commercial_state": "reserved",
                "reserved_until": reservation.reserved_until,
                "reserved_to_agency_id": reservation.agency_id,
                "sold_at": None,
            }

        return {
            "commercial_state": "available",
            "reserved_until": None,
            "reserved_to_agency_id": None,
            "sold_at": None,
        }

    @classmethod
    def reserve_lead(cls, db: Session, lead_id: str, agency_id: str, hours: int = 72) -> dict:
        settings = get_settings()
        if not settings.feature_reservations:
            raise ApiException(
                status_code=400,
                code="FEATURE_DISABLED",
                message="Reservas desactivadas por configuracion.",
                details={"feature": "reservations"},
            )

        if hours <= 0:
            raise ApiException(
                status_code=400,
                code="VALIDATION_ERROR",
                message="hours debe ser mayor que 0.",
                details={"field": "hours"},
            )

        cls._get_lead_or_404(db, lead_id)
        cls._get_active_agency_or_404(db, agency_id)

        tier = cls._lead_tier(db, lead_id)
        if tier != "A":
            raise ApiException(
                status_code=400,
                code="RESERVATION_ONLY_TIER_A",
                message="Solo se permite reserva en leads Tier A.",
                details={"lead_id": lead_id, "tier": tier},
            )

        sale = cls._sale_for_lead(db, lead_id)
        if sale:
            raise ApiException(
                status_code=409,
                code="SOLD",
                message="Lead ya vendido.",
                details={"lead_id": lead_id},
            )

        reservation = cls._normalize_reservation_state(db, cls._reservation_for_lead(db, lead_id))
        if reservation and reservation.status == "active":
            raise ApiException(
                status_code=409,
                code="RESERVED",
                message="Lead ya reservado.",
                details={"lead_id": lead_id, "agency_id": reservation.agency_id},
            )

        now = _now()
        reserved_until = now + timedelta(hours=hours)
        if reservation:
            reservation.agency_id = agency_id
            reservation.reserved_at = now
            reservation.reserved_until = reserved_until
            reservation.status = "active"
            reservation.released_at = None
        else:
            reservation = LeadReservation(
                id=str(uuid4()),
                lead_id=lead_id,
                agency_id=agency_id,
                reserved_at=now,
                reserved_until=reserved_until,
                status="active",
            )
            db.add(reservation)

        db.commit()
        db.refresh(reservation)
        return {
            "lead_id": lead_id,
            "agency_id": agency_id,
            "reserved_until": reservation.reserved_until,
            "status": "active",
        }

    @classmethod
    def release_reservation(cls, db: Session, lead_id: str) -> dict:
        cls._get_lead_or_404(db, lead_id)
        reservation = cls._reservation_for_lead(db, lead_id)
        if not reservation:
            raise ApiException(
                status_code=404,
                code="NOT_FOUND",
                message="Reserva no encontrada para el lead.",
                details={"lead_id": lead_id},
            )

        reservation.status = "released"
        reservation.released_at = _now()
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return {"lead_id": lead_id, "status": "released"}

    @classmethod
    def sell_lead(cls, db: Session, lead_id: str, agency_id: str, price_eur: int, notes: str | None = None) -> dict:
        if price_eur <= 0:
            raise ApiException(
                status_code=400,
                code="VALIDATION_ERROR",
                message="price_eur debe ser mayor que 0.",
                details={"field": "price_eur"},
            )

        lead = cls._get_lead_or_404(db, lead_id)
        cls._get_active_agency_or_404(db, agency_id)

        existing_sale = cls._sale_for_lead(db, lead_id)
        if existing_sale:
            raise ApiException(
                status_code=409,
                code="SOLD",
                message="Lead ya vendido.",
                details={"lead_id": lead_id},
            )

        reservation = cls._normalize_reservation_state(db, cls._reservation_for_lead(db, lead_id))
        if reservation and reservation.status == "active" and reservation.agency_id != agency_id:
            raise ApiException(
                status_code=409,
                code="RESERVED_FOR_OTHER",
                message="Lead reservado por otra agencia.",
                details={"lead_id": lead_id, "agency_id": reservation.agency_id},
            )

        tier = cls._lead_tier(db, lead_id) or "D"
        now = _now()
        sale = LeadSale(
            id=str(uuid4()),
            lead_id=lead_id,
            agency_id=agency_id,
            sold_at=now,
            tier=tier,
            price_eur=price_eur,
            notes=notes,
        )
        db.add(sale)

        lead.status = "vendido"
        lead.updated_at = now
        db.add(lead)

        if reservation and reservation.status == "active":
            reservation.status = "released"
            reservation.released_at = now
            db.add(reservation)

        db.commit()
        db.refresh(sale)
        return {
            "lead_id": lead_id,
            "agency_id": agency_id,
            "sold_at": sale.sold_at,
            "price_eur": sale.price_eur,
            "tier": tier,
        }

    @classmethod
    def export_sales_csv(
        cls,
        db: Session,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
        zone_key: str | None,
        agency_id: str | None,
        tier: str | None,
    ) -> str:
        query = (
            db.query(LeadSale, Lead, Agency, PropertyInput, IEIResultRecord)
            .join(Lead, Lead.id == LeadSale.lead_id)
            .join(Agency, Agency.id == LeadSale.agency_id)
            .join(PropertyInput, PropertyInput.lead_id == Lead.id)
            .join(IEIResultRecord, IEIResultRecord.lead_id == Lead.id)
        )

        if date_from:
            query = query.filter(LeadSale.sold_at >= date_from)
        if date_to:
            query = query.filter(LeadSale.sold_at <= date_to)
        if zone_key:
            query = query.filter(PropertyInput.zone_key == zone_key.lower().strip())
        if agency_id:
            query = query.filter(LeadSale.agency_id == agency_id)
        if tier:
            query = query.filter(LeadSale.tier == tier)

        rows = query.order_by(LeadSale.sold_at.desc()).all()
        settings = get_settings()

        out = StringIO()
        writer = csv.writer(out)
        writer.writerow(
            [
                "sold_at",
                "lead_id",
                "agency_id",
                "agency_name",
                "zone_key",
                "tier",
                "segment",
                "pricing_policy",
                "lead_price_eur",
                "price_eur",
                "iei_score",
                "iei_framework_version",
                "powered_by",
                "owner_phone_masked",
                "owner_email_masked",
            ]
        )

        for sale, lead, agency, prop, iei in rows:
            writer.writerow(
                [
                    sale.sold_at.isoformat() if sale.sold_at else "",
                    lead.id,
                    agency.id,
                    agency.name,
                    prop.zone_key,
                    sale.tier,
                    lead.segment or sale.tier,
                    lead.pricing_policy or "",
                    lead.lead_price_eur if lead.lead_price_eur is not None else "",
                    sale.price_eur,
                    iei.iei_score,
                    ((iei.lead_card_json or {}).get("iei_framework") or {}).get("version") or IEI_FRAMEWORK_VERSION,
                    (iei.lead_card_json or {}).get("powered_by") or IEI_POWERED_BY,
                    _mask_phone(lead.owner_phone, export_pii=settings.export_pii),
                    _mask_email(lead.owner_email, export_pii=settings.export_pii),
                ]
            )

        return out.getvalue()
