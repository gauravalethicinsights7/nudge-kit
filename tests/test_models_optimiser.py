from datetime import date

import pytest

from models.optimiser import optimise_mix
from schemas.base import ProvMoney
from schemas.channel import Channel, ResponseCurve
from schemas.enums import CurveSource, Origin


def _channel(ref, lam=0.3, alpha=0.8, gamma=20.0, beta=100.0, unit_cost=1.0, capacity=None) -> Channel:
    return Channel(
        channel_ref=ref,
        name=ref,
        unit="unit",
        unit_cost=ProvMoney(value=unit_cost, source="t", origin=Origin.internal, as_of=date.today(), confidence=0.9, currency="INR"),
        capacity=capacity,
        curve=ResponseCurve.model_validate({"lambda": lam, "alpha": alpha, "gamma": gamma, "beta": beta, "source": CurveSource.prior}),
    )


def test_optimise_mix_respects_budget():
    channels = [_channel("a"), _channel("b")]
    fit_scores = {"a": 1.0, "b": 1.0}
    results = optimise_mix(channels, fit_scores, budget=100.0, hcp_count=50)
    assert sum(r.spend for r in results) <= 100.0 + 1e-6


def test_optimise_mix_respects_capacity():
    channels = [_channel("a", capacity=5.0, unit_cost=1.0)]
    results = optimise_mix(channels, {"a": 1.0}, budget=1000.0, hcp_count=50)
    assert results[0].activity <= 5.0 + 1e-6


def test_optimise_mix_respects_frequency_cap():
    channels = [_channel("a", unit_cost=1.0)]
    # freq cap of 2 touches/HCP/month x 10 HCPs = 20 units max
    results = optimise_mix(channels, {"a": 1.0}, budget=10_000.0, hcp_count=10, freq_caps={"a": 2.0})
    assert results[0].activity <= 20.0 + 1e-6


def test_optimise_mix_excludes_compliance_forbidden_channel():
    channels = [_channel("a"), _channel("b")]
    results = optimise_mix(
        channels, {"a": 1.0, "b": 1.0}, budget=100.0, hcp_count=50,
        compliance_allowed={"a": True, "b": False},
    )
    b_result = next(r for r in results if r.channel_id == "b")
    assert b_result.spend == 0.0
    assert b_result.activity == 0.0


def test_optimise_mix_zero_budget_allocates_nothing():
    channels = [_channel("a")]
    results = optimise_mix(channels, {"a": 1.0}, budget=0.0, hcp_count=50)
    assert results[0].spend == 0.0


def test_optimise_mix_equal_marginal_roi_at_interior_optimum():
    # Two channels with the SAME response shape and fit -> at an unconstrained
    # interior optimum, marginal ROI should equalize across both (the classic
    # KKT condition for an interior maximum of a concave separable objective).
    channels = [_channel("a", lam=0.3, alpha=0.8, gamma=20.0, beta=100.0), _channel("b", lam=0.3, alpha=0.8, gamma=20.0, beta=100.0)]
    results = optimise_mix(channels, {"a": 1.0, "b": 1.0}, budget=200.0, hcp_count=1000)
    a_roi = next(r for r in results if r.channel_id == "a").marginal_roi
    b_roi = next(r for r in results if r.channel_id == "b").marginal_roi
    assert a_roi == pytest.approx(b_roi, rel=0.05)  # spec's own 5% tolerance
