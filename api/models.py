from __future__ import annotations

from sqlalchemy import JSON, Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from api.db import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True)
    status = Column(String(20), nullable=False, default="nuevo")

    owner_name = Column(Text)
    owner_email = Column(Text)
    owner_phone = Column(Text)

    consent_contact = Column(Boolean, nullable=False)
    consent_text_version = Column(Text)
    consent_timestamp = Column(DateTime(timezone=True))

    source_campaign = Column(Text)
    utm_source = Column(Text)
    utm_medium = Column(Text)
    utm_campaign = Column(Text)
    utm_term = Column(Text)
    utm_content = Column(Text)

    ip_hash = Column(Text)
    phone_hash = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("status in ('nuevo','contactado','cita','vendido','descartado')", name="ck_leads_status"),
        CheckConstraint("consent_contact = true", name="ck_leads_consent_true"),
    )


class PropertyInput(Base):
    __tablename__ = "property_inputs"

    id = Column(String(36), primary_key=True)
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True)

    zone_key = Column(Text, nullable=False)
    municipality = Column(Text, nullable=False)
    neighborhood = Column(Text)
    postal_code = Column(Text)

    property_type = Column(Text, nullable=False)
    m2 = Column(Float, nullable=False)
    condition = Column(Text, nullable=False)
    year_built = Column(Integer)

    has_elevator = Column(Boolean, nullable=False, default=False)
    has_terrace = Column(Boolean, nullable=False, default=False)
    terrace_m2 = Column(Float)
    has_parking = Column(Boolean, nullable=False, default=False)
    has_views = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OwnerSignal(Base):
    __tablename__ = "owner_signals"

    id = Column(String(36), primary_key=True)
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True)

    sale_horizon = Column(Text, nullable=False)
    motivation = Column(Text, nullable=False)
    already_listed = Column(Text, nullable=False)
    exclusivity = Column(Text, nullable=False)
    expected_price = Column(Float)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class IEIResultRecord(Base):
    __tablename__ = "iei_results"

    id = Column(String(36), primary_key=True)
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)

    iei_score = Column(Integer, nullable=False)
    tier = Column(String(1), nullable=False)

    breakdown_intencion = Column(Integer, nullable=False)
    breakdown_precio = Column(Integer, nullable=False)
    breakdown_mercado = Column(Integer, nullable=False)

    base_per_m2 = Column(Float, nullable=False)
    base_price = Column(Float, nullable=False)
    adjusted_price = Column(Float, nullable=False)
    range_low = Column(Float, nullable=False)
    range_high = Column(Float, nullable=False)
    demand_level = Column(Text, nullable=False)

    pricing_expected_price = Column(Float)
    pricing_delta = Column(Float)
    pricing_gap_percent = Column(Float)
    pricing_note = Column(Text)

    recommendation = Column(Text, nullable=False)

    applied_factors_json = Column(JSON, nullable=False)
    lead_card_json = Column(JSON, nullable=False)

    engine_version = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Zone(Base):
    __tablename__ = "zones"

    id = Column(String(36), primary_key=True)
    zone_key = Column(Text, nullable=False, unique=True)
    municipality = Column(Text, nullable=False)

    base_per_m2 = Column(Float, nullable=False)
    demand_level = Column(Text, nullable=False)

    type_factor_overrides = Column(JSON)
    condition_factor_overrides = Column(JSON)
    extras_add_overrides = Column(JSON)
    extras_cap_override = Column(Float)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Agency(Base):
    __tablename__ = "agencies"

    id = Column(String(36), primary_key=True)
    name = Column(Text, nullable=False)
    email = Column(Text)
    phone = Column(Text)
    municipality_focus = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LeadReservation(Base):
    __tablename__ = "lead_reservations"

    id = Column(String(36), primary_key=True)
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True)
    agency_id = Column(String(36), ForeignKey("agencies.id"), nullable=False)
    reserved_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reserved_until = Column(DateTime(timezone=True), nullable=False)
    status = Column(Text, nullable=False, default="active")
    released_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("status in ('active','released','expired')", name="ck_lead_reservations_status"),
    )


class LeadSale(Base):
    __tablename__ = "lead_sales"

    id = Column(String(36), primary_key=True)
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True)
    agency_id = Column(String(36), ForeignKey("agencies.id"), nullable=False)
    sold_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    tier = Column(Text, nullable=False)
    price_eur = Column(Integer, nullable=False)
    notes = Column(Text)


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True)
    event_name = Column(Text, nullable=False)
    event_version = Column(Text, nullable=False)
    session_id = Column(Text, nullable=False)
    lead_id = Column(String(36))
    payload_json = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PrivacyDeleteRequest(Base):
    __tablename__ = "privacy_delete_requests"

    id = Column(String(36), primary_key=True)
    email = Column(Text)
    phone = Column(Text)
    request_text = Column(Text)
    status = Column(Text, nullable=False, default="nuevo")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
