# iei_engine.py
# IEI Inmobiliario (MVP) — Motor de scoring y estimación de rango de precio
#
# Objetivo:
# - Calcular un IEI Score (0–100) que clasifica oportunidades de captación (propietario + inmueble)
# - Estimar un rango de precio realista (conservador) basado en €/m² por zona + factores
# - Generar un "Lead Card" listo para vender a inmobiliarias
#
# Nota:
# - Este motor es determinista (reglas + tablas). En fases posteriores puedes reemplazar
#   BASE_PRICE_PER_M2 y DEMAND_INDEX por datos externos o modelos estadísticos.

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, Optional, Tuple
import math


# -----------------------------
# Enums / Tipos
# -----------------------------

class PropertyType(str, Enum):
    PISO = "piso"
    ATICO = "atico"
    PLANTA_BAJA = "planta_baja"
    CASA_ADOSADA = "casa_adosada"
    CHALET = "chalet"


class PropertyCondition(str, Enum):
    REFORMADO = "reformado"
    BUEN_ESTADO = "buen_estado"
    A_REFORMAR_PARCIAL = "a_reformar_parcial"
    A_REFORMAR_INTEGRAL = "a_reformar_integral"


class SaleHorizon(str, Enum):
    MENOS_3 = "<3m"
    ENTRE_3_6 = "3-6m"
    ENTRE_6_12 = "6-12m"
    VALORANDO = "valorando"


class Motivation(str, Enum):
    TRASLADO = "traslado"
    HERENCIA = "herencia"
    DIVORCIO = "divorcio"
    FINANZAS = "finanzas"
    MEJORA = "mejora"
    COMPRA_OTRA = "compra_otra"
    INVERSION = "inversion"
    CURIOSIDAD = "curiosidad"
    OTRO = "otro"


class ListingStatus(str, Enum):
    NO = "no"
    SI_CON_AGENCIA = "si_con_agencia"
    SI_POR_SU_CUENTA = "si_por_su_cuenta"


class ExclusivityDisposition(str, Enum):
    SI = "si"
    DEPENDE = "depende"
    NO = "no"


class DemandLevel(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class Tier(str, Enum):
    A = "A"  # Hot / alta probabilidad
    B = "B"  # Bueno
    C = "C"  # Nurture
    D = "D"  # Descartar / remarketing


# -----------------------------
# Inputs del motor
# -----------------------------

@dataclass(frozen=True)
class PropertyFeatures:
    zone_key: str                 # Ej: "castelldefels", "gava", "sitges" (clave interna)
    municipality: str             # Texto libre para mostrar
    neighborhood: Optional[str]   # Texto libre para mostrar (opcional)
    postal_code: Optional[str]    # Opcional
    property_type: PropertyType
    m2: float
    condition: PropertyCondition
    year_built: Optional[int] = None

    has_elevator: bool = False
    has_terrace: bool = False
    terrace_m2: Optional[float] = None
    has_parking: bool = False
    has_views: bool = False


@dataclass(frozen=True)
class OwnerSignals:
    sale_horizon: SaleHorizon
    motivation: Motivation
    already_listed: ListingStatus
    exclusivity: ExclusivityDisposition
    expected_price: Optional[float]  # expectativa del propietario (EUR). Puede ser None.


@dataclass(frozen=True)
class LeadInput:
    property: PropertyFeatures
    owner: OwnerSignals


# -----------------------------
# Outputs del motor
# -----------------------------

@dataclass(frozen=True)
class PriceEstimate:
    base_per_m2: float
    base_price: float
    adjusted_price: float
    range_low: float
    range_high: float
    demand_level: DemandLevel
    applied_factors: Dict[str, float]


@dataclass(frozen=True)
class IEIResult:
    iei_score: int
    tier: Tier
    breakdown: Dict[str, int]  # {"intencion": x, "precio": y, "mercado": z}
    price_estimate: PriceEstimate
    pricing_alignment: Dict[str, Any]  # delta, expected_price, gap_percent, note
    recommendation: str


# -----------------------------
# Tablas (MVP)
# -----------------------------
#
# IMPORTANTE:
# - Sustituye estos valores por datos reales por zona cuando los tengas.
# - Para MVP: arranca con 2–3 zonas piloto y ajusta con feedback de agencias.

BASE_PRICE_PER_M2: Dict[str, float] = {
    # Base conservadora (más cerca de cierre que de anuncio)
    "castelldefels": 3350.0,
    "gava": 3100.0,
    "sitges": 4100.0,
}

DEMAND_INDEX: Dict[str, DemandLevel] = {
    "castelldefels": DemandLevel.ALTA,
    "gava": DemandLevel.MEDIA,
    "sitges": DemandLevel.ALTA,
}

TYPE_FACTOR: Dict[PropertyType, float] = {
    PropertyType.PISO: 1.00,
    PropertyType.ATICO: 1.08,
    PropertyType.PLANTA_BAJA: 0.93,
    PropertyType.CASA_ADOSADA: 1.05,
    PropertyType.CHALET: 1.12,
}

CONDITION_FACTOR: Dict[PropertyCondition, float] = {
    PropertyCondition.REFORMADO: 1.08,
    PropertyCondition.BUEN_ESTADO: 1.00,
    PropertyCondition.A_REFORMAR_PARCIAL: 0.92,
    PropertyCondition.A_REFORMAR_INTEGRAL: 0.85,
}

# Extras: sumatorios con cap (para evitar inflar el precio)
EXTRAS_ADD: Dict[str, float] = {
    "elevator": 0.04,
    "terrace_big": 0.03,   # >10 m²
    "terrace_small": 0.02, # <=10 m² (si has_terrace true pero no terrace_m2)
    "parking": 0.04,
    "views": 0.06,
}
EXTRAS_CAP = 0.10  # máximo +10% acumulado


# -----------------------------
# Helpers
# -----------------------------

def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def _round_price(x: float) -> float:
    # redondeo “humano” para credibilidad (a múltiplos de 500€)
    return float(int(round(x / 500.0) * 500))


def _demand_points(level: DemandLevel) -> int:
    return {DemandLevel.ALTA: 12, DemandLevel.MEDIA: 8, DemandLevel.BAJA: 4}[level]


def _type_points(t: PropertyType) -> int:
    # puntos de "vendibilidad" por tipología (no es precio)
    return {
        PropertyType.PISO: 8,
        PropertyType.ATICO: 10,
        PropertyType.CASA_ADOSADA: 10,
        PropertyType.CHALET: 10,
        PropertyType.PLANTA_BAJA: 5,
    }[t]


def _condition_points(c: PropertyCondition) -> int:
    return {
        PropertyCondition.REFORMADO: 8,
        PropertyCondition.BUEN_ESTADO: 6,
        PropertyCondition.A_REFORMAR_PARCIAL: 3,
        PropertyCondition.A_REFORMAR_INTEGRAL: 2,
    }[c]


def _extras_points(p: PropertyFeatures) -> int:
    # cap a 4 puntos
    pts = 0
    if p.has_elevator:
        pts += 1
    if p.has_parking:
        pts += 1
    if p.has_terrace:
        pts += 1
    if p.has_views:
        pts += 1
    return min(4, pts)


# -----------------------------
# Precio (rango conservador)
# -----------------------------

def estimate_price(p: PropertyFeatures) -> PriceEstimate:
    zone = p.zone_key.lower().strip()
    if zone not in BASE_PRICE_PER_M2:
        raise ValueError(f"Zona no configurada: {zone}")

    base_per_m2 = BASE_PRICE_PER_M2[zone]
    demand_level = DEMAND_INDEX.get(zone, DemandLevel.MEDIA)

    base_price = p.m2 * base_per_m2

    factors: Dict[str, float] = {}
    f_type = TYPE_FACTOR[p.property_type]
    f_cond = CONDITION_FACTOR[p.condition]
    factors["type"] = f_type
    factors["condition"] = f_cond

    extras_add = 0.0
    if p.has_elevator:
        extras_add += EXTRAS_ADD["elevator"]
        factors["extra_elevator"] = 1.0 + EXTRAS_ADD["elevator"]
    if p.has_parking:
        extras_add += EXTRAS_ADD["parking"]
        factors["extra_parking"] = 1.0 + EXTRAS_ADD["parking"]
    if p.has_views:
        extras_add += EXTRAS_ADD["views"]
        factors["extra_views"] = 1.0 + EXTRAS_ADD["views"]

    if p.has_terrace:
        if p.terrace_m2 is not None and p.terrace_m2 > 10:
            extras_add += EXTRAS_ADD["terrace_big"]
            factors["extra_terrace"] = 1.0 + EXTRAS_ADD["terrace_big"]
        else:
            extras_add += EXTRAS_ADD["terrace_small"]
            factors["extra_terrace"] = 1.0 + EXTRAS_ADD["terrace_small"]

    extras_add = _clamp(extras_add, 0.0, EXTRAS_CAP)
    extras_factor = 1.0 + extras_add
    factors["extras_factor_capped"] = extras_factor

    adjusted = base_price * f_type * f_cond * extras_factor

    # Rango: conservador y asimétrico
    low = adjusted * 0.97   # -3%
    high = adjusted * 1.05  # +5%

    return PriceEstimate(
        base_per_m2=base_per_m2,
        base_price=_round_price(base_price),
        adjusted_price=_round_price(adjusted),
        range_low=_round_price(low),
        range_high=_round_price(high),
        demand_level=demand_level,
        applied_factors=factors,
    )


# -----------------------------
# Scoring IEI (0–100)
# -----------------------------

def _intention_score(o: OwnerSignals) -> int:
    pts = 0

    # Horizonte
    pts += {
        SaleHorizon.MENOS_3: 18,
        SaleHorizon.ENTRE_3_6: 14,
        SaleHorizon.ENTRE_6_12: 8,
        SaleHorizon.VALORANDO: 0,
    }[o.sale_horizon]

    # Motivo (evento de vida = más intención)
    pts += {
        Motivation.TRASLADO: 10,
        Motivation.HERENCIA: 10,
        Motivation.DIVORCIO: 10,
        Motivation.FINANZAS: 10,
        Motivation.MEJORA: 7,
        Motivation.COMPRA_OTRA: 7,
        Motivation.INVERSION: 4,
        Motivation.CURIOSIDAD: 0,
        Motivation.OTRO: 4,
    }[o.motivation]

    # Ya está en mercado
    pts += {
        ListingStatus.NO: 4,
        ListingStatus.SI_CON_AGENCIA: 2,
        ListingStatus.SI_POR_SU_CUENTA: 3,
    }[o.already_listed]

    # Exclusiva
    pts += {
        ExclusivityDisposition.SI: 8,
        ExclusivityDisposition.DEPENDE: 4,
        ExclusivityDisposition.NO: 0,
    }[o.exclusivity]

    return int(_clamp(pts, 0, 40))


def _price_alignment_score(expected_price: Optional[float], est: PriceEstimate) -> Tuple[int, Dict[str, Any]]:
    # Si no hay expectativa, penaliza moderado (no “castigar” demasiado, pero reduce valor comercial)
    if expected_price is None or expected_price <= 0:
        return 10, {
            "expected_price": expected_price,
            "estimated_range": (est.range_low, est.range_high),
            "delta": None,
            "gap_percent": None,
            "note": "Sin expectativa de precio: alineación parcial (menor precisión comercial).",
        }

    # Tomamos como referencia el precio ajustado (centro del rango)
    ref = est.adjusted_price
    delta = (expected_price - ref) / ref  # positivo = sobreprecio

    # Score por tramos (conservador: el sobreprecio destruye ventabilidad)
    if delta <= 0.05:
        score = 30
    elif delta <= 0.10:
        score = 22
    elif delta <= 0.15:
        score = 14
    elif delta <= 0.25:
        score = 6
    else:
        score = 0

    # Si está muy por debajo, no damos 30 porque puede esconder problemas (venta rápida, pero no “premium”)
    if delta < -0.10:
        score = 20

    gap_percent = round(delta * 100, 1)

    note = "Expectativa alineada con mercado." if score >= 22 else "Expectativa por encima del mercado: puede alargar venta."
    if delta < -0.10:
        note = "Expectativa por debajo del mercado: podría vender rápido, revisar condiciones."

    return score, {
        "expected_price": _round_price(expected_price),
        "estimated_range": (est.range_low, est.range_high),
        "delta": delta,
        "gap_percent": gap_percent,
        "note": note,
    }


def _market_score(p: PropertyFeatures, est: PriceEstimate) -> int:
    # 0–30
    pts = 0
    pts += _demand_points(est.demand_level)                 # 4/8/12
    pts += _type_points(p.property_type)                    # 5/8/10
    pts += _condition_points(p.condition)                   # 2/3/6/8
    pts += _extras_points(p)                                # 0–4
    return int(_clamp(pts, 0, 30))


def _tier_from_score(score: int) -> Tier:
    if score >= 85:
        return Tier.A
    if score >= 70:
        return Tier.B
    if score >= 55:
        return Tier.C
    return Tier.D


def _recommendation(score: int, price_note: str, est: PriceEstimate, o: OwnerSignals) -> str:
    # Recomendación orientada a acción (propietario + utilidad para inmobiliaria)
    if score >= 85:
        return "Alta ventabilidad. Recomendada estrategia de venta activa y propuesta de exclusiva (plan claro + calendario)."
    if score >= 70:
        return f"Ventabilidad buena. {price_note} Recomendado preparar inmueble y definir estrategia de precio para acelerar."
    if score >= 55:
        return f"Ventabilidad media. {price_note} Recomendado ajustar expectativas y mejorar presentación antes de salir al mercado."
    return f"Ventabilidad baja. {price_note} Recomendado revisar precio/condición o esperar a un mejor momento de mercado."


def compute_iei(lead: LeadInput) -> IEIResult:
    est = estimate_price(lead.property)

    s_int = _intention_score(lead.owner)
    s_price, align = _price_alignment_score(lead.owner.expected_price, est)
    s_market = _market_score(lead.property, est)

    total = int(_clamp(s_int + s_price + s_market, 0, 100))
    tier = _tier_from_score(total)

    rec = _recommendation(total, align.get("note", ""), est, lead.owner)

    return IEIResult(
        iei_score=total,
        tier=tier,
        breakdown={"intencion": s_int, "precio": s_price, "mercado": s_market},
        price_estimate=est,
        pricing_alignment=align,
        recommendation=rec,
    )


# -----------------------------
# Lead Card (para inmobiliarias)
# -----------------------------

def lead_card(lead: LeadInput, result: IEIResult) -> Dict[str, Any]:
    p = lead.property
    o = lead.owner
    est = result.price_estimate
    align = result.pricing_alignment

    return {
        "iei_score": result.iei_score,
        "tier": result.tier.value,
        "breakdown": result.breakdown,
        "zone": {
            "zone_key": p.zone_key,
            "municipality": p.municipality,
            "neighborhood": p.neighborhood,
            "postal_code": p.postal_code,
            "demand_level": est.demand_level.value,
        },
        "property": {
            "type": p.property_type.value,
            "m2": p.m2,
            "condition": p.condition.value,
            "year_built": p.year_built,
            "extras": {
                "elevator": p.has_elevator,
                "terrace": p.has_terrace,
                "terrace_m2": p.terrace_m2,
                "parking": p.has_parking,
                "views": p.has_views,
            },
        },
        "pricing": {
            "estimated_range": [est.range_low, est.range_high],
            "estimated_center": est.adjusted_price,
            "owner_expected": align.get("expected_price"),
            "gap_percent": align.get("gap_percent"),
            "note": align.get("note"),
        },
        "owner_signals": {
            "sale_horizon": o.sale_horizon.value,
            "motivation": o.motivation.value,
            "already_listed": o.already_listed.value,
            "exclusivity": o.exclusivity.value,
        },
        "recommendation": result.recommendation,
    }


# -----------------------------
# Ejemplo rápido (manual)
# -----------------------------
if __name__ == "__main__":
    lead = LeadInput(
        property=PropertyFeatures(
            zone_key="castelldefels",
            municipality="Castelldefels",
            neighborhood="Centro",
            postal_code="08860",
            property_type=PropertyType.PISO,
            m2=90,
            condition=PropertyCondition.BUEN_ESTADO,
            has_elevator=True,
            has_terrace=True,
            terrace_m2=8,
            has_parking=False,
            has_views=False,
        ),
        owner=OwnerSignals(
            sale_horizon=SaleHorizon.ENTRE_3_6,
            motivation=Motivation.COMPRA_OTRA,
            already_listed=ListingStatus.NO,
            exclusivity=ExclusivityDisposition.DEPENDE,
            expected_price=380000,
        ),
    )

    res = compute_iei(lead)
    card = lead_card(lead, res)

    print("IEI:", res.iei_score, "Tier:", res.tier.value)
    print("Breakdown:", res.breakdown)
    print("Precio estimado:", res.price_estimate.range_low, "-", res.price_estimate.range_high)
    print("Gap %:", res.pricing_alignment.get("gap_percent"), "|", res.pricing_alignment.get("note"))
    print("Lead card keys:", list(card.keys()))
