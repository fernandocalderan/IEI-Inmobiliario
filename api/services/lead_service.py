from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from api.errors import ApiException
from api.iei_framework import IEI_POWERED_BY
from api.models import IEIResultRecord, Lead, OwnerSignal, PropertyInput
from api.schemas import LeadCreateRequestSchema
from api.services.commercial_service import CommercialService
from api.services.iei_service import build_lead_card, compute_pricing_from_result, get_framework_metadata, score_lead
from api.settings import get_settings
from api.utils.ip_hash import hash_phone


class LeadService:
    @staticmethod
    def create_lead(db: Session, payload: LeadCreateRequestSchema, ip_hash: str) -> dict:
        if not payload.lead.consent_contact:
            raise ApiException(
                status_code=400,
                code="CONSENT_REQUIRED",
                message="Se requiere consentimiento para crear el lead.",
                details={},
            )

        now = datetime.now(UTC)
        settings = get_settings()
        phone_hash = hash_phone(payload.lead.owner_phone or "") if payload.lead.owner_phone else None
        zone_key = payload.input.property.zone_key.lower().strip()

        if settings.dedupe_window_days > 0 and phone_hash:
            cutoff = now - timedelta(days=settings.dedupe_window_days)
            duplicate = (
                db.query(Lead.id)
                .join(PropertyInput, PropertyInput.lead_id == Lead.id)
                .filter(
                    Lead.phone_hash == phone_hash,
                    PropertyInput.zone_key == zone_key,
                    Lead.created_at >= cutoff,
                )
                .order_by(Lead.created_at.desc())
                .first()
            )
            if duplicate:
                return {
                    "duplicate": True,
                    "existing_lead_id": duplicate[0],
                    "note": "DUPLICATE_PHONE_ZONE_30D",
                }

        lead_input, raw_result, result = score_lead(db, payload.input)
        lead_card = build_lead_card(lead_input, raw_result)
        pricing = compute_pricing_from_result(db, payload.input, result, confidence_bucket=None)
        framework = get_framework_metadata()
        pricing_public = {
            "lead_price_eur": pricing["lead_price_eur"],
            "segment": pricing["segment"],
            "policy": pricing["policy"],
            "confidence_bucket": pricing["confidence_bucket"],
        }
        result["pricing"] = pricing_public
        if framework:
            result["iei_framework"] = framework
        lead_card["pricing_lead"] = pricing_public
        if framework:
            lead_card["iei_framework"] = framework
            lead_card["powered_by"] = IEI_POWERED_BY

        lead_id = str(uuid4())

        lead_row = Lead(
            id=lead_id,
            status="nuevo",
            owner_name=payload.lead.owner_name,
            owner_email=payload.lead.owner_email,
            owner_phone=payload.lead.owner_phone,
            consent_contact=payload.lead.consent_contact,
            consent_text_version=payload.lead.consent_text_version,
            consent_timestamp=now,
            source_campaign=payload.lead.source_campaign,
            utm_source=payload.lead.utm_source,
            utm_medium=payload.lead.utm_medium,
            utm_campaign=payload.lead.utm_campaign,
            utm_term=payload.lead.utm_term,
            utm_content=payload.lead.utm_content,
            ip_hash=ip_hash,
            phone_hash=phone_hash,
            pricing_policy=pricing["policy"],
            is_premium_zone=bool(pricing["is_premium_zone"]),
            lead_price_eur=pricing["lead_price_eur"],
            segment=pricing["segment"],
            confidence_bucket=pricing["confidence_bucket"],
            created_at=now,
            updated_at=now,
        )

        property_row = PropertyInput(
            id=str(uuid4()),
            lead_id=lead_id,
            zone_key=lead_input.property.zone_key,
            municipality=lead_input.property.municipality,
            neighborhood=lead_input.property.neighborhood,
            postal_code=lead_input.property.postal_code,
            property_type=lead_input.property.property_type.value,
            m2=lead_input.property.m2,
            condition=lead_input.property.condition.value,
            year_built=lead_input.property.year_built,
            has_elevator=lead_input.property.has_elevator,
            has_terrace=lead_input.property.has_terrace,
            terrace_m2=lead_input.property.terrace_m2,
            has_parking=lead_input.property.has_parking,
            has_views=lead_input.property.has_views,
            created_at=now,
        )

        owner_row = OwnerSignal(
            id=str(uuid4()),
            lead_id=lead_id,
            sale_horizon=lead_input.owner.sale_horizon.value,
            motivation=lead_input.owner.motivation.value,
            already_listed=lead_input.owner.already_listed.value,
            exclusivity=lead_input.owner.exclusivity.value,
            expected_price=lead_input.owner.expected_price,
            created_at=now,
        )

        alignment = result["pricing_alignment"]
        price = result["price_estimate"]

        iei_row = IEIResultRecord(
            id=str(uuid4()),
            lead_id=lead_id,
            iei_score=result["iei_score"],
            tier=result["tier"],
            breakdown_intencion=result["breakdown"]["intencion"],
            breakdown_precio=result["breakdown"]["precio"],
            breakdown_mercado=result["breakdown"]["mercado"],
            base_per_m2=price["base_per_m2"],
            base_price=price["base_price"],
            adjusted_price=price["adjusted_price"],
            range_low=price["range_low"],
            range_high=price["range_high"],
            demand_level=price["demand_level"],
            pricing_expected_price=alignment.get("expected_price"),
            pricing_delta=alignment.get("delta"),
            pricing_gap_percent=alignment.get("gap_percent"),
            pricing_note=alignment.get("note"),
            recommendation=result["recommendation"],
            applied_factors_json=price.get("applied_factors", {}),
            lead_card_json=lead_card,
            pricing_json={
                "policy": pricing["policy"],
                "policy_version": pricing["policy_version"],
                "segment": pricing["segment"],
                "lead_price_eur": pricing["lead_price_eur"],
                "confidence_bucket": pricing["confidence_bucket"],
                "is_premium_zone": pricing["is_premium_zone"],
                "policy_snapshot": pricing["policy_json"],
                "iei_framework_version": framework["version"] if framework else None,
                "powered_by": IEI_POWERED_BY if framework else None,
            },
            engine_version=settings.engine_version,
            created_at=now,
        )

        try:
            db.add(lead_row)
            db.add(property_row)
            db.add(owner_row)
            db.add(iei_row)
            db.commit()
        except Exception:
            db.rollback()
            raise

        response_lead_card = {
            "iei_score": result["iei_score"],
            "tier": result["tier"],
            "lead_price_eur": pricing["lead_price_eur"],
            "segment": pricing["segment"],
            "policy": pricing["policy"],
            "confidence_bucket": pricing["confidence_bucket"],
        }
        if framework:
            response_lead_card["iei_framework"] = framework
            response_lead_card["powered_by"] = IEI_POWERED_BY

        return {
            "lead_id": lead_id,
            "status": "nuevo",
            "result": {"iei_score": result["iei_score"], "tier": result["tier"]},
            "lead_card": response_lead_card,
            "pricing": pricing_public,
            "iei_framework": framework,
            "created_at": now,
        }

    @staticmethod
    def list_leads(
        db: Session,
        *,
        tier: str | None,
        zone_key: str | None,
        sale_horizon: str | None,
        status: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        page: int,
        page_size: int,
    ) -> dict:
        query = (
            db.query(Lead, PropertyInput, OwnerSignal, IEIResultRecord)
            .join(PropertyInput, PropertyInput.lead_id == Lead.id)
            .join(OwnerSignal, OwnerSignal.lead_id == Lead.id)
            .join(IEIResultRecord, IEIResultRecord.lead_id == Lead.id)
        )

        if tier:
            query = query.filter(IEIResultRecord.tier == tier)
        if zone_key:
            query = query.filter(PropertyInput.zone_key == zone_key.lower().strip())
        if sale_horizon:
            query = query.filter(OwnerSignal.sale_horizon == sale_horizon)
        if status:
            query = query.filter(Lead.status == status)
        if date_from:
            query = query.filter(Lead.created_at >= date_from)
        if date_to:
            query = query.filter(Lead.created_at <= date_to)

        total = query.count()
        rows = (
            query.order_by(Lead.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for lead, prop, owner, res in rows:
            commercial = CommercialService.get_commercial_state(db, lead.id)
            items.append(
                {
                    "lead_id": lead.id,
                    "created_at": lead.created_at,
                    "status": lead.status,
                    "tier": res.tier,
                    "iei_score": res.iei_score,
                    "zone_key": prop.zone_key,
                    "sale_horizon": owner.sale_horizon,
                    "owner_name": lead.owner_name,
                    "owner_phone": lead.owner_phone,
                    "commercial_state": commercial["commercial_state"],
                    "reserved_until": commercial["reserved_until"],
                    "reserved_to_agency_id": commercial["reserved_to_agency_id"],
                    "sold_at": commercial["sold_at"],
                    "lead_price_eur": lead.lead_price_eur,
                    "segment": lead.segment,
                    "pricing_policy": lead.pricing_policy,
                    "is_premium_zone": bool(lead.is_premium_zone),
                    "confidence_bucket": lead.confidence_bucket,
                }
            )

        return {"items": items, "page": page, "page_size": page_size, "total": total}

    @staticmethod
    def get_lead_detail(db: Session, lead_id: str) -> dict:
        row = (
            db.query(Lead, PropertyInput, OwnerSignal, IEIResultRecord)
            .join(PropertyInput, PropertyInput.lead_id == Lead.id)
            .join(OwnerSignal, OwnerSignal.lead_id == Lead.id)
            .join(IEIResultRecord, IEIResultRecord.lead_id == Lead.id)
            .filter(Lead.id == lead_id)
            .first()
        )

        if not row:
            raise ApiException(
                status_code=404,
                code="NOT_FOUND",
                message="Lead no encontrado.",
                details={"lead_id": lead_id},
            )

        lead, prop, owner, result = row
        commercial = CommercialService.get_commercial_state(db, lead.id)

        return {
            "lead_id": lead.id,
            "created_at": lead.created_at,
            "status": lead.status,
            "owner": {
                "name": lead.owner_name,
                "email": lead.owner_email,
                "phone": lead.owner_phone,
            },
            "zone_key": prop.zone_key,
            "sale_horizon": owner.sale_horizon,
            "tier": result.tier,
            "iei_score": result.iei_score,
            "lead_card": result.lead_card_json,
            "commercial_state": commercial["commercial_state"],
            "reserved_until": commercial["reserved_until"],
            "reserved_to_agency_id": commercial["reserved_to_agency_id"],
            "sold_at": commercial["sold_at"],
            "pricing": {
                "lead_price_eur": lead.lead_price_eur,
                "segment": lead.segment,
                "policy": lead.pricing_policy,
                "confidence_bucket": lead.confidence_bucket,
                "is_premium_zone": bool(lead.is_premium_zone),
            },
            "iei_framework": (result.lead_card_json or {}).get("iei_framework"),
            "powered_by": (result.lead_card_json or {}).get("powered_by"),
        }

    @staticmethod
    def update_status(db: Session, lead_id: str, new_status: str) -> dict:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ApiException(
                status_code=404,
                code="NOT_FOUND",
                message="Lead no encontrado.",
                details={"lead_id": lead_id},
            )

        lead.status = new_status
        lead.updated_at = datetime.now(UTC)

        db.add(lead)
        db.commit()
        db.refresh(lead)

        return {
            "lead_id": lead.id,
            "status": lead.status,
            "updated_at": lead.updated_at,
        }
