from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


PropertyTypeLiteral = Literal["piso", "atico", "planta_baja", "casa_adosada", "chalet"]
PropertyConditionLiteral = Literal["reformado", "buen_estado", "a_reformar_parcial", "a_reformar_integral"]
SaleHorizonLiteral = Literal["<3m", "3-6m", "6-12m", "valorando"]
MotivationLiteral = Literal[
    "traslado",
    "herencia",
    "divorcio",
    "finanzas",
    "mejora",
    "compra_otra",
    "inversion",
    "curiosidad",
    "otro",
]
ListingStatusLiteral = Literal["no", "si_con_agencia", "si_por_su_cuenta"]
ExclusivityLiteral = Literal["si", "depende", "no"]
DemandLevelLiteral = Literal["alta", "media", "baja"]
TierLiteral = Literal["A", "B", "C", "D"]
LeadStatusLiteral = Literal["nuevo", "contactado", "cita", "vendido", "descartado"]
CommercialStateLiteral = Literal["available", "reserved", "sold"]


class PropertyFeaturesSchema(BaseModel):
    zone_key: str
    municipality: str
    neighborhood: Optional[str] = None
    postal_code: Optional[str] = None

    property_type: PropertyTypeLiteral
    m2: float
    condition: PropertyConditionLiteral
    year_built: Optional[int] = None

    has_elevator: bool = False
    has_terrace: bool = False
    terrace_m2: Optional[float] = None
    has_parking: bool = False
    has_views: bool = False


class OwnerSignalsSchema(BaseModel):
    sale_horizon: SaleHorizonLiteral
    motivation: MotivationLiteral
    already_listed: ListingStatusLiteral
    exclusivity: ExclusivityLiteral
    expected_price: Optional[float] = None


class LeadInputSchema(BaseModel):
    property: PropertyFeaturesSchema
    owner: OwnerSignalsSchema


class PriceEstimateSchema(BaseModel):
    base_per_m2: float
    base_price: float
    adjusted_price: float
    range_low: float
    range_high: float
    demand_level: DemandLevelLiteral
    applied_factors: dict[str, float]


class PricingAlignmentSchema(BaseModel):
    expected_price: Optional[float] = None
    estimated_range: list[float]
    delta: Optional[float] = None
    gap_percent: Optional[float] = None
    note: str


class IEIResultSchema(BaseModel):
    iei_score: int
    tier: TierLiteral
    breakdown: dict[str, int]
    price_estimate: PriceEstimateSchema
    pricing_alignment: PricingAlignmentSchema
    recommendation: str


class LeadCreateInfoSchema(BaseModel):
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None

    consent_contact: bool
    consent_text_version: Optional[str] = None

    source_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None


class LeadCreateRequestSchema(BaseModel):
    lead: LeadCreateInfoSchema
    input: LeadInputSchema
    company_website: Optional[str] = None


class LeadCreateResponseSchema(BaseModel):
    lead_id: str
    status: LeadStatusLiteral
    result: dict[str, Any]
    lead_card: dict[str, Any]
    created_at: datetime


class LeadDuplicateResponseSchema(BaseModel):
    duplicate: Literal[True]
    existing_lead_id: str
    note: str


class AdminLeadItemSchema(BaseModel):
    lead_id: str
    created_at: datetime
    status: LeadStatusLiteral
    tier: Optional[TierLiteral] = None
    iei_score: Optional[int] = None
    zone_key: Optional[str] = None
    sale_horizon: Optional[SaleHorizonLiteral] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    commercial_state: CommercialStateLiteral = "available"
    reserved_until: Optional[datetime] = None
    reserved_to_agency_id: Optional[str] = None
    sold_at: Optional[datetime] = None


class AdminLeadListResponseSchema(BaseModel):
    items: list[AdminLeadItemSchema]
    page: int
    page_size: int
    total: int


class UpdateLeadStatusRequestSchema(BaseModel):
    status: LeadStatusLiteral


class UpdateLeadStatusResponseSchema(BaseModel):
    lead_id: str
    status: LeadStatusLiteral
    updated_at: datetime


class ReserveLeadRequestSchema(BaseModel):
    agency_id: str
    hours: int = 72


class ReserveLeadResponseSchema(BaseModel):
    lead_id: str
    agency_id: str
    reserved_until: datetime
    status: Literal["active"]


class ReleaseReservationRequestSchema(BaseModel):
    reason: Optional[str] = None


class ReleaseReservationResponseSchema(BaseModel):
    lead_id: str
    status: Literal["released"]


class SellLeadRequestSchema(BaseModel):
    agency_id: str
    price_eur: int
    notes: Optional[str] = None


class SellLeadResponseSchema(BaseModel):
    lead_id: str
    agency_id: str
    sold_at: datetime
    price_eur: int
    tier: TierLiteral


class AgencyItemSchema(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    municipality_focus: Optional[str] = None
    is_active: bool


class AgenciesListResponseSchema(BaseModel):
    items: list[AgencyItemSchema]


class ZoneItemSchema(BaseModel):
    id: str
    zone_key: str
    municipality: str
    base_per_m2: float
    demand_level: DemandLevelLiteral
    type_factor_overrides: Optional[dict[str, float]] = None
    condition_factor_overrides: Optional[dict[str, float]] = None
    extras_add_overrides: Optional[dict[str, float]] = None
    extras_cap_override: Optional[float] = None
    is_active: bool


class ZonesListResponseSchema(BaseModel):
    items: list[ZoneItemSchema]


class ZonePatchRequestSchema(BaseModel):
    base_per_m2: Optional[float] = None
    demand_level: Optional[DemandLevelLiteral] = None
    type_factor_overrides: Optional[dict[str, float]] = None
    condition_factor_overrides: Optional[dict[str, float]] = None
    extras_add_overrides: Optional[dict[str, float]] = None
    extras_cap_override: Optional[float] = None
    is_active: Optional[bool] = None


class ZonePatchResponseSchema(BaseModel):
    zone_key: str
    base_per_m2: float
    demand_level: DemandLevelLiteral
    updated_at: datetime


class EventRequestSchema(BaseModel):
    event_name: str
    event_version: str = "v1"
    session_id: str = Field(min_length=1)
    lead_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class EventResponseSchema(BaseModel):
    ok: bool
    deduplicated: bool = False


class PrivacyDeleteRequestSchema(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    request_text: Optional[str] = None


class PrivacyDeleteResponseSchema(BaseModel):
    ok: bool
    request_id: str


class AdminLoginRequestSchema(BaseModel):
    password: str


class AdminLoginResponseSchema(BaseModel):
    ok: bool


class ErrorBodySchema(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelopeSchema(BaseModel):
    error: ErrorBodySchema
