#!/usr/bin/env python3
"""Stress test y simulacion reproducible para el motor IEI (sin tocar iei_engine.py)."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Optional

# Permite ejecutar el script desde /tools sin instalar paquete.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from iei_engine import (
    BASE_PRICE_PER_M2,
    ExclusivityDisposition,
    LeadInput,
    ListingStatus,
    Motivation,
    OwnerSignals,
    PropertyCondition,
    PropertyFeatures,
    PropertyType,
    SaleHorizon,
    compute_iei,
    estimate_price,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulador de leads sintéticos para IEI")
    parser.add_argument("--seed", type=int, default=42, help="Semilla reproducible")
    parser.add_argument("--n", type=int, default=500, help="Cantidad de leads sintéticos")
    parser.add_argument(
        "--zones",
        type=str,
        default=",".join(BASE_PRICE_PER_M2.keys()),
        help="Lista de zonas separadas por coma",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="tools/out/sim_results.csv",
        help="Ruta de salida CSV",
    )
    parser.add_argument(
        "--input-json",
        type=str,
        default=None,
        help="Ruta opcional a dataset manual de leads (mismo shape que LeadInput)",
    )
    return parser.parse_args()


def weighted_choice(rng: random.Random, items: Iterable[Any], weights: Iterable[float]) -> Any:
    return rng.choices(list(items), weights=list(weights), k=1)[0]


def truncated_normal(rng: random.Random, mu: float, sigma: float, lo: float, hi: float) -> float:
    while True:
        val = rng.gauss(mu, sigma)
        if lo <= val <= hi:
            return round(val, 1)


def maybe(rng: random.Random, probability: float) -> bool:
    return rng.random() < probability


def zone_defaults(zone_key: str) -> Dict[str, Any]:
    defaults = {
        "castelldefels": {
            "municipality": "Castelldefels",
            "postal_codes": ["08860", "08859"],
            "neighborhoods": ["Centro", "Montmar", "Can Bou", "Bellamar"],
        },
        "gava": {
            "municipality": "Gava",
            "postal_codes": ["08850"],
            "neighborhoods": ["Centro", "Gava Mar", "Can Tries", "Les Colomeres"],
        },
        "sitges": {
            "municipality": "Sitges",
            "postal_codes": ["08870"],
            "neighborhoods": ["Centre", "Aiguadolc", "Vinyet", "Poble Sec"],
        },
    }
    if zone_key in defaults:
        return defaults[zone_key]
    clean = zone_key.replace("_", " ").strip()
    return {
        "municipality": clean.title() if clean else "Unknown",
        "postal_codes": [None],
        "neighborhoods": [None],
    }


def generate_property(rng: random.Random, zone_key: str) -> PropertyFeatures:
    ptype = weighted_choice(
        rng,
        [
            PropertyType.PISO,
            PropertyType.ATICO,
            PropertyType.PLANTA_BAJA,
            PropertyType.CASA_ADOSADA,
            PropertyType.CHALET,
        ],
        [0.60, 0.12, 0.08, 0.11, 0.09],
    )

    condition = weighted_choice(
        rng,
        [
            PropertyCondition.BUEN_ESTADO,
            PropertyCondition.REFORMADO,
            PropertyCondition.A_REFORMAR_PARCIAL,
            PropertyCondition.A_REFORMAR_INTEGRAL,
        ],
        [0.56, 0.23, 0.15, 0.06],
    )

    size = truncated_normal(rng, mu=90, sigma=22, lo=60, hi=140)

    # Probabilidades de extras por tipología
    elevator_prob = {
        PropertyType.PISO: 0.78,
        PropertyType.ATICO: 0.82,
        PropertyType.PLANTA_BAJA: 0.55,
        PropertyType.CASA_ADOSADA: 0.18,
        PropertyType.CHALET: 0.10,
    }[ptype]

    terrace_prob = {
        PropertyType.PISO: 0.40,
        PropertyType.ATICO: 0.85,
        PropertyType.PLANTA_BAJA: 0.45,
        PropertyType.CASA_ADOSADA: 0.72,
        PropertyType.CHALET: 0.68,
    }[ptype]

    parking_prob = {
        PropertyType.PISO: 0.35,
        PropertyType.ATICO: 0.45,
        PropertyType.PLANTA_BAJA: 0.30,
        PropertyType.CASA_ADOSADA: 0.58,
        PropertyType.CHALET: 0.62,
    }[ptype]

    views_prob = {
        PropertyType.PISO: 0.22,
        PropertyType.ATICO: 0.45,
        PropertyType.PLANTA_BAJA: 0.18,
        PropertyType.CASA_ADOSADA: 0.25,
        PropertyType.CHALET: 0.30,
    }[ptype]

    has_terrace = maybe(rng, terrace_prob)
    terrace_m2: Optional[float] = None
    if has_terrace:
        if maybe(rng, 0.35):
            terrace_m2 = round(rng.uniform(12, 40), 1)
        else:
            terrace_m2 = round(rng.uniform(4, 10), 1)

    defaults = zone_defaults(zone_key)
    postal = weighted_choice(rng, defaults["postal_codes"], [1.0] * len(defaults["postal_codes"]))
    neighborhood = weighted_choice(
        rng,
        defaults["neighborhoods"],
        [1.0] * len(defaults["neighborhoods"]),
    )

    year_built = None if maybe(rng, 0.25) else int(rng.uniform(1965, 2022))

    return PropertyFeatures(
        zone_key=zone_key,
        municipality=defaults["municipality"],
        neighborhood=neighborhood,
        postal_code=postal,
        property_type=ptype,
        m2=size,
        condition=condition,
        year_built=year_built,
        has_elevator=maybe(rng, elevator_prob),
        has_terrace=has_terrace,
        terrace_m2=terrace_m2,
        has_parking=maybe(rng, parking_prob),
        has_views=maybe(rng, views_prob),
    )


def generate_owner(rng: random.Random, prop: PropertyFeatures) -> OwnerSignals:
    sale_horizon = weighted_choice(
        rng,
        [
            SaleHorizon.MENOS_3,
            SaleHorizon.ENTRE_3_6,
            SaleHorizon.ENTRE_6_12,
            SaleHorizon.VALORANDO,
        ],
        [0.22, 0.37, 0.26, 0.15],
    )

    motivation = weighted_choice(
        rng,
        [
            Motivation.TRASLADO,
            Motivation.HERENCIA,
            Motivation.DIVORCIO,
            Motivation.FINANZAS,
            Motivation.MEJORA,
            Motivation.COMPRA_OTRA,
            Motivation.INVERSION,
            Motivation.CURIOSIDAD,
            Motivation.OTRO,
        ],
        [0.14, 0.11, 0.08, 0.07, 0.20, 0.19, 0.10, 0.06, 0.05],
    )

    already_listed = weighted_choice(
        rng,
        [ListingStatus.NO, ListingStatus.SI_CON_AGENCIA, ListingStatus.SI_POR_SU_CUENTA],
        [0.62, 0.17, 0.21],
    )

    exclusivity = weighted_choice(
        rng,
        [ExclusivityDisposition.SI, ExclusivityDisposition.DEPENDE, ExclusivityDisposition.NO],
        [0.34, 0.46, 0.20],
    )

    expected_price: Optional[float]
    if maybe(rng, 0.12):
        expected_price = None
    else:
        delta_bucket = weighted_choice(rng, [-0.15, -0.05, 0.05, 0.10, 0.20, 0.30], [0.10, 0.20, 0.26, 0.20, 0.16, 0.08])
        delta = delta_bucket + rng.uniform(-0.01, 0.01)
        try:
            ref = estimate_price(prop).adjusted_price
            expected_price = round(ref * (1.0 + delta), 2)
        except ValueError:
            # Si la zona no existe, mantenemos expected_price para forzar test de error del harness.
            expected_price = round(max(50000.0, prop.m2 * 3000.0 * (1.0 + delta)), 2)

    return OwnerSignals(
        sale_horizon=sale_horizon,
        motivation=motivation,
        already_listed=already_listed,
        exclusivity=exclusivity,
        expected_price=expected_price,
    )


def generate_synthetic_leads(rng: random.Random, n: int, zones: List[str]) -> List[LeadInput]:
    leads: List[LeadInput] = []
    for _ in range(n):
        zone_key = weighted_choice(rng, zones, [1.0] * len(zones))
        prop = generate_property(rng, zone_key)
        owner = generate_owner(rng, prop)
        leads.append(LeadInput(property=prop, owner=owner))
    return leads


def parse_enum(enum_cls: Any, value: Any) -> Any:
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)


def lead_from_dict(raw: Dict[str, Any]) -> LeadInput:
    p = raw["property"]
    o = raw["owner"]

    prop = PropertyFeatures(
        zone_key=p["zone_key"],
        municipality=p["municipality"],
        neighborhood=p.get("neighborhood"),
        postal_code=p.get("postal_code"),
        property_type=parse_enum(PropertyType, p["property_type"]),
        m2=float(p["m2"]),
        condition=parse_enum(PropertyCondition, p["condition"]),
        year_built=p.get("year_built"),
        has_elevator=bool(p.get("has_elevator", False)),
        has_terrace=bool(p.get("has_terrace", False)),
        terrace_m2=p.get("terrace_m2"),
        has_parking=bool(p.get("has_parking", False)),
        has_views=bool(p.get("has_views", False)),
    )

    owner = OwnerSignals(
        sale_horizon=parse_enum(SaleHorizon, o["sale_horizon"]),
        motivation=parse_enum(Motivation, o["motivation"]),
        already_listed=parse_enum(ListingStatus, o["already_listed"]),
        exclusivity=parse_enum(ExclusivityDisposition, o["exclusivity"]),
        expected_price=o.get("expected_price"),
    )

    return LeadInput(property=prop, owner=owner)


def load_manual_leads(path: str) -> List[LeadInput]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("El archivo JSON debe contener una lista de leads")
    return [lead_from_dict(item) for item in data]


def safe_gap_percent(result: Dict[str, Any]) -> Optional[float]:
    gap = result.get("pricing_alignment", {}).get("gap_percent")
    return float(gap) if gap is not None else None


def evaluate_leads(leads: List[LeadInput]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for lead in leads:
        prop = lead.property
        owner = lead.owner
        row: Dict[str, Any] = {
            "zone_key": prop.zone_key,
            "municipality": prop.municipality,
            "m2": prop.m2,
            "property_type": prop.property_type.value,
            "condition": prop.condition.value,
            "has_elevator": prop.has_elevator,
            "has_terrace": prop.has_terrace,
            "terrace_m2": prop.terrace_m2,
            "has_parking": prop.has_parking,
            "has_views": prop.has_views,
            "sale_horizon": owner.sale_horizon.value,
            "motivation": owner.motivation.value,
            "already_listed": owner.already_listed.value,
            "exclusivity": owner.exclusivity.value,
            "expected_price": owner.expected_price,
            "adjusted_price": None,
            "range_low": None,
            "range_high": None,
            "gap_percent": None,
            "iei_score": None,
            "tier": None,
            "breakdown_intencion": None,
            "breakdown_precio": None,
            "breakdown_mercado": None,
            "combo_key": None,
            "error": None,
        }

        try:
            result = compute_iei(lead)
            row.update(
                {
                    "adjusted_price": result.price_estimate.adjusted_price,
                    "range_low": result.price_estimate.range_low,
                    "range_high": result.price_estimate.range_high,
                    "gap_percent": result.pricing_alignment.get("gap_percent"),
                    "iei_score": result.iei_score,
                    "tier": result.tier.value,
                    "breakdown_intencion": result.breakdown["intencion"],
                    "breakdown_precio": result.breakdown["precio"],
                    "breakdown_mercado": result.breakdown["mercado"],
                }
            )
            combo = (
                prop.zone_key,
                prop.property_type.value,
                prop.condition.value,
                owner.sale_horizon.value,
                owner.already_listed.value,
            )
            row["combo_key"] = "|".join(combo)
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc)

        rows.append(row)

    return rows


def write_csv(rows: List[Dict[str, Any]], out_path: str) -> None:
    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "zone_key",
        "municipality",
        "m2",
        "property_type",
        "condition",
        "has_elevator",
        "has_terrace",
        "terrace_m2",
        "has_parking",
        "has_views",
        "sale_horizon",
        "motivation",
        "already_listed",
        "exclusivity",
        "expected_price",
        "adjusted_price",
        "range_low",
        "range_high",
        "gap_percent",
        "iei_score",
        "tier",
        "breakdown_intencion",
        "breakdown_precio",
        "breakdown_mercado",
        "combo_key",
        "error",
    ]

    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_report(rows: List[Dict[str, Any]]) -> None:
    valid = [r for r in rows if not r["error"]]
    errors = [r for r in rows if r["error"]]

    print("\n=== IEI Simulation Report ===")
    print(f"Leads evaluados: {len(rows)}")
    print(f"Leads validos: {len(valid)}")
    print(f"Leads con error: {len(errors)}")

    tier_counts = Counter(r["tier"] for r in valid if r["tier"])
    print("\nConteo por tier:")
    for tier in ["A", "B", "C", "D"]:
        print(f"  Tier {tier}: {tier_counts.get(tier, 0)}")

    scores_by_tier: Dict[str, List[int]] = defaultdict(list)
    for row in valid:
        scores_by_tier[row["tier"]].append(int(row["iei_score"]))

    print("\nMedia / mediana score por tier:")
    for tier in ["A", "B", "C", "D"]:
        scores = scores_by_tier.get(tier, [])
        if scores:
            print(f"  Tier {tier}: media={mean(scores):.2f} mediana={median(scores):.2f}")
        else:
            print(f"  Tier {tier}: sin datos")

    gaps = [float(r["gap_percent"]) for r in valid if r["gap_percent"] is not None]
    if gaps:
        above_15 = sum(1 for g in gaps if g > 15)
        pct = 100.0 * above_15 / len(gaps)
        print(f"\n% leads con gap > 15%: {pct:.2f}% ({above_15}/{len(gaps)})")
    else:
        print("\n% leads con gap > 15%: sin datos")

    tier_a_combos = Counter(r["combo_key"] for r in valid if r["tier"] == "A" and r["combo_key"])
    print("\nTop 10 combinaciones que mas generan Tier A:")
    if tier_a_combos:
        for combo, count in tier_a_combos.most_common(10):
            print(f"  {count:4d}  {combo}")
    else:
        print("  No hay leads Tier A en esta corrida.")

    if errors:
        print("\nErrores detectados (primeros 5):")
        for row in errors[:5]:
            print(f"  zone={row['zone_key']} type={row['property_type']} error={row['error']}")


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    zones = [z.strip().lower() for z in args.zones.split(",") if z.strip()]
    if not zones:
        raise ValueError("Debes indicar al menos una zona")

    leads: List[LeadInput] = []
    if args.n > 0:
        leads.extend(generate_synthetic_leads(rng, args.n, zones))

    if args.input_json:
        leads.extend(load_manual_leads(args.input_json))

    if not leads:
        raise ValueError("No hay leads para procesar: usa --n > 0 o --input-json")

    rows = evaluate_leads(leads)
    write_csv(rows, args.out)
    print_report(rows)

    print(f"\nCSV generado en: {Path(args.out).resolve()}")
    print("Configuracion:")
    print(f"  seed={args.seed}")
    print(f"  synthetic_n={args.n}")
    print(f"  zones={','.join(zones)}")
    if args.input_json:
        print(f"  input_json={args.input_json}")


if __name__ == "__main__":
    main()

# python tools/simulate_leads.py --n 500 --seed 42 --out tools/out/sim.csv
# pytest -q
