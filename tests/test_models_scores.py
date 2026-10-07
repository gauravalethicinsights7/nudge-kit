from datetime import date

import pytest

from models.scores import (
    assign_rung,
    assign_tier,
    build_reason,
    estimate_potential,
    opportunity,
    p_move_up,
    percentile_rank,
    reachability,
    resolve_potential,
)
from packs.loader import load_pack
from schemas.base import ProvNumber
from schemas.enums import Access, Origin, Rung, Tier
from schemas.hcp import HCP, Consent, ExternalIds, Geo
from tests.factories import make_brand

AS_OF = date(2026, 9, 30)


@pytest.fixture
def india_pack():
    return load_pack("india")


def _hcp(**overrides) -> HCP:
    defaults = dict(
        external_ids=ExternalIds(crm_id="c1"),
        name_hash="h1",
        specialty="diabetologist",
        setting="clinic",
        geo=Geo(city_tier="metro"),
        potential=ProvNumber(value=0.0, source="x", origin=Origin.estimated, as_of=AS_OF, confidence=0.0),
        brand_share=ProvNumber(value=0.05, source="x", origin=Origin.estimated, as_of=AS_OF, confidence=0.5),
        access=Access.open,
        consent=Consent(),
    )
    defaults.update(overrides)
    return HCP(**defaults)


# ---- estimate_potential / resolve_potential ----


def test_estimate_potential_uses_volume_and_category_weights(india_pack):
    hcp = _hcp(specialty="endocrinologist", setting="hospital", geo=Geo(city_tier="metro"), patient_volume_estimate=100.0)
    result = estimate_potential(hcp, india_pack.potential_proxies, AS_OF)
    assert result.value == pytest.approx(100.0 * 1.0 * 1.0 * 1.0)
    assert result.confidence == 0.5
    assert result.origin == Origin.estimated


def test_estimate_potential_missing_volume_signal_uses_lower_confidence(india_pack):
    hcp = _hcp(patient_volume_estimate=None)
    result = estimate_potential(hcp, india_pack.potential_proxies, AS_OF)
    assert result.value == pytest.approx(1.0 * 0.8 * 1.0)  # diabetologist x clinic x metro
    assert result.confidence < 0.5


def test_estimate_potential_unknown_category_defaults_neutral(india_pack):
    hcp = _hcp(specialty="unlisted_specialty", patient_volume_estimate=10.0)
    result = estimate_potential(hcp, india_pack.potential_proxies, AS_OF)
    assert result.value == pytest.approx(10.0 * 1.0 * 0.8 * 1.0)  # neutral specialty weight


def test_estimate_potential_handles_missing_potential_proxies():
    hcp = _hcp(patient_volume_estimate=5.0)
    result = estimate_potential(hcp, None, AS_OF)
    assert result.value == pytest.approx(5.0)  # all weights neutral


def test_resolve_potential_passes_through_measured_value(india_pack):
    measured = ProvNumber(value=999.0, source="rx_audit", origin=Origin.external, as_of=AS_OF, confidence=0.9)
    hcp = _hcp(potential=measured)
    result = resolve_potential(hcp, india_pack.potential_proxies, AS_OF)
    assert result is measured


def test_resolve_potential_estimates_when_unmeasured(india_pack):
    hcp = _hcp(patient_volume_estimate=50.0)  # potential defaults to origin=estimated
    result = resolve_potential(hcp, india_pack.potential_proxies, AS_OF)
    assert result.origin == Origin.estimated
    assert result.value > 0


# ---- assign_rung / p_move_up ----


def test_assign_rung_falls_back_to_unknown_aware(india_pack):
    hcp = _hcp()
    brand = make_brand()
    state = assign_rung(hcp, brand.id, india_pack, AS_OF)
    assert state.rung == Rung.aware
    assert state.rung_confidence == 0.3
    assert state.measured is False
    assert state.brand_id == brand.id
    assert state.hcp_id == hcp.id


def test_p_move_up_reads_pack_priors(india_pack):
    assert p_move_up(Rung.considering, india_pack) == pytest.approx(0.10)


def test_p_move_up_defaults_zero_for_uncovered_rung(india_pack):
    # neither pack's rung_transition_monthly covers advocate/lapsed
    assert p_move_up(Rung.advocate, india_pack) == 0.0
    assert p_move_up(Rung.lapsed, india_pack) == 0.0


# ---- reachability ----


def test_reachability_neutral_channel_factor_without_persona(india_pack):
    assert reachability(Access.open, india_pack) == pytest.approx(1.0)
    assert reachability(Access.restricted, india_pack) == pytest.approx(0.6)


def test_reachability_no_access_gives_floor(india_pack):
    assert reachability(Access.no_see, india_pack) == pytest.approx(0.2)


# ---- opportunity ----


def test_opportunity_zero_when_share_already_at_or_above_target():
    assert opportunity(potential=100, target_share=0.05, current_share=0.10, p_move_up_value=0.5, reachability_value=1.0) == 0.0
    assert opportunity(potential=100, target_share=0.05, current_share=0.05, p_move_up_value=0.5, reachability_value=1.0) == 0.0


def test_opportunity_positive_when_gap_exists():
    value = opportunity(potential=100, target_share=0.10, current_share=0.02, p_move_up_value=0.2, reachability_value=0.5)
    assert value == pytest.approx(100 * 0.08 * 0.2 * 0.5)


# ---- percentile_rank ----


def test_percentile_rank_single_value_population_is_median():
    assert percentile_rank(5.0, [5.0]) == 50.0
    assert percentile_rank(5.0, []) == 50.0


def test_percentile_rank_orders_correctly():
    population = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert percentile_rank(50.0, population) == 100.0
    assert percentile_rank(10.0, population) == pytest.approx(20.0)


# ---- assign_tier ----


def test_assign_tier_t1_grow_when_high_potential_share_gap_and_early_rung(india_pack):
    tier = assign_tier(
        potential_percentile=80, current_share=0.01, target_share=0.05,
        rung=Rung.considering, reachability_value=1.0, pack=india_pack,
    )
    assert tier == Tier.t1_grow


def test_assign_tier_t2_defend_when_high_potential_and_adopter(india_pack):
    tier = assign_tier(
        potential_percentile=80, current_share=0.10, target_share=0.05,
        rung=Rung.adopter, reachability_value=1.0, pack=india_pack,
    )
    assert tier == Tier.t2_defend


def test_assign_tier_t3_develop_when_mid_potential_and_reachable(india_pack):
    tier = assign_tier(
        potential_percentile=50, current_share=0.01, target_share=0.05,
        rung=Rung.unaware, reachability_value=0.7, pack=india_pack,
    )
    assert tier == Tier.t3_develop


def test_assign_tier_t4_nurture_fallback(india_pack):
    tier = assign_tier(
        potential_percentile=10, current_share=0.01, target_share=0.05,
        rung=Rung.unaware, reachability_value=0.1, pack=india_pack,
    )
    assert tier == Tier.t4_nurture


# ---- build_reason ----


def test_build_reason_is_nonempty_and_mentions_key_numbers():
    reason = build_reason(
        potential=100.0, potential_percentile=80.0, current_share=0.02, target_share=0.05,
        rung=Rung.considering, p_move_up_value=0.1, reachability_value=0.6, opportunity_value=1.8,
    )
    assert reason.strip()
    assert "considering" in reason
    assert "80" in reason
