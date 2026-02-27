import pytest

from iei_engine import (
    EXTRAS_CAP,
    ExclusivityDisposition,
    LeadInput,
    ListingStatus,
    Motivation,
    OwnerSignals,
    PropertyCondition,
    PropertyFeatures,
    PropertyType,
    SaleHorizon,
    Tier,
    _tier_from_score,
    compute_iei,
    estimate_price,
)


def make_property(**overrides):
    base = dict(
        zone_key="castelldefels",
        municipality="Castelldefels",
        neighborhood="Centro",
        postal_code="08860",
        property_type=PropertyType.PISO,
        m2=90,
        condition=PropertyCondition.BUEN_ESTADO,
        year_built=1998,
        has_elevator=True,
        has_terrace=True,
        terrace_m2=8,
        has_parking=False,
        has_views=False,
    )
    base.update(overrides)
    return PropertyFeatures(**base)


def make_owner(expected_price, **overrides):
    base = dict(
        sale_horizon=SaleHorizon.ENTRE_3_6,
        motivation=Motivation.COMPRA_OTRA,
        already_listed=ListingStatus.NO,
        exclusivity=ExclusivityDisposition.DEPENDE,
        expected_price=expected_price,
    )
    base.update(overrides)
    return OwnerSignals(**base)


def make_lead(prop_overrides=None, owner_overrides=None, expected_price=380000):
    prop_overrides = prop_overrides or {}
    owner_overrides = owner_overrides or {}
    prop = make_property(**prop_overrides)
    owner = make_owner(expected_price=expected_price, **owner_overrides)
    return LeadInput(property=prop, owner=owner)


def test_zone_not_configured_raises():
    lead = make_lead(prop_overrides={"zone_key": "zona_inexistente"})
    with pytest.raises(ValueError, match="Zona no configurada"):
        compute_iei(lead)


def test_tier_thresholds():
    assert _tier_from_score(85) == Tier.A
    assert _tier_from_score(70) == Tier.B
    assert _tier_from_score(55) == Tier.C
    assert _tier_from_score(54) == Tier.D


def test_extras_cap_does_not_exceed():
    prop = make_property(
        property_type=PropertyType.CHALET,
        has_elevator=True,
        has_terrace=True,
        terrace_m2=25,
        has_parking=True,
        has_views=True,
    )
    est = estimate_price(prop)
    extras_factor = est.applied_factors["extras_factor_capped"]

    assert extras_factor <= 1.0 + EXTRAS_CAP


def test_price_alignment_gap_buckets_behave():
    prop = make_property()
    ref = estimate_price(prop).adjusted_price

    res_ref = compute_iei(make_lead(prop_overrides={}, expected_price=ref))
    res_mid = compute_iei(make_lead(prop_overrides={}, expected_price=ref * 1.12))
    res_high = compute_iei(make_lead(prop_overrides={}, expected_price=ref * 1.30))

    score_ref = res_ref.breakdown["precio"]
    score_mid = res_mid.breakdown["precio"]
    score_high = res_high.breakdown["precio"]

    assert score_ref > score_mid > score_high
