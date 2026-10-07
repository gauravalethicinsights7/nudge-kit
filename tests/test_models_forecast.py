from uuid import uuid4

from models.forecast import (
    DEFAULT_MARGIN_ASSUMPTION,
    DEFAULT_PERSISTENCE_ASSUMPTION,
    build_scenarios,
    compute_delta_nrx,
    compute_revenue_and_roi,
    tornado_sensitivity,
)
from packs.loader import load_pack
from schemas.enums import Rung, Tier
from schemas.hcp import Segment


def _segment(total_potential=1000.0, target_share=0.10, avg_share=0.02) -> Segment:
    return Segment(
        brand_id=uuid4(),
        name="Seg",
        rule={},
        tier=Tier.t1_grow,
        hcp_count=100,
        total_potential=total_potential,
        avg_share=avg_share,
        target_share=target_share,
    )


def test_compute_delta_nrx_uses_pack_prior_for_from_rung():
    pack = load_pack("india")
    segment = _segment()
    delta = compute_delta_nrx(segment, Rung.considering, pack, persistence=1.0)
    expected_p_move = pack.priors.rung_transition_monthly["considering"]
    assert delta == 1000.0 * 0.08 * expected_p_move * 1.0


def test_compute_delta_nrx_zero_for_uncovered_rung():
    pack = load_pack("india")
    segment = _segment()
    assert compute_delta_nrx(segment, Rung.advocate, pack, persistence=1.0) == 0.0


def test_compute_revenue_and_roi_none_without_incremental_spend():
    revenue, roi = compute_revenue_and_roi(100.0, net_price=50.0, currency="INR", margin=0.5, incremental_spend=None)
    assert revenue.value == 5000.0
    assert roi is None


def test_compute_revenue_and_roi_computed_with_incremental_spend():
    revenue, roi = compute_revenue_and_roi(
        100.0, net_price=50.0, currency="INR", margin=0.5, incremental_spend=1000.0
    )
    assert roi == (5000.0 * 0.5 - 1000.0) / 1000.0


def test_tornado_sensitivity_ranks_highest_swing_first():
    assumptions = {
        "big_swing": (100.0, 0.1),  # low confidence -> wide swing
        "small_swing": (100.0, 0.95),  # high confidence -> narrow swing
    }

    def compute_fn(overrides):
        return overrides["big_swing"] + overrides["small_swing"]

    results = tornado_sensitivity(assumptions, compute_fn, top_n=2)
    assert results[0].name == "big_swing"
    assert results[0].swing > results[1].swing


def test_build_scenarios_produces_three_scenarios_with_assumptions():
    pack = load_pack("india")
    segment = _segment()
    forecast = build_scenarios(
        [(segment, Rung.considering)], pack, net_price=100.0, currency="INR", budget_envelope=None
    )
    assert forecast.base.roi is None  # no budget_envelope given
    assert len(forecast.base.assumptions) == 3
    assert forecast.upside.delta_nrx > forecast.base.delta_nrx
    assert forecast.downside.delta_nrx < forecast.base.delta_nrx


def test_build_scenarios_computes_roi_when_budget_given():
    pack = load_pack("india")
    segment = _segment()
    forecast = build_scenarios(
        [(segment, Rung.considering)], pack, net_price=100.0, currency="INR", budget_envelope=10000.0
    )
    assert forecast.base.roi is not None


def test_build_scenarios_defaults_are_tracked_as_low_confidence_assumptions():
    pack = load_pack("india")
    segment = _segment()
    forecast = build_scenarios(
        [(segment, Rung.considering)], pack, net_price=100.0, currency="INR", budget_envelope=None
    )
    by_name = {a.name: a for a in forecast.base.assumptions}
    assert by_name["persistence"].value == DEFAULT_PERSISTENCE_ASSUMPTION
    assert by_name["margin"].value == DEFAULT_MARGIN_ASSUMPTION
    assert by_name["persistence"].confidence < 0.5
    assert by_name["margin"].confidence < 0.5
