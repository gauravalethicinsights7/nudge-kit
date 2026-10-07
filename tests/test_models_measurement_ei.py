from datetime import date, timedelta
from uuid import uuid4

import numpy as np
import pytest

from models.measurement import (
    DEFAULT_EI_WEIGHTS,
    MIN_SAMPLES_FOR_WEIGHT_FIT,
    EIComponents,
    compute_ei,
    compute_ei_components,
    fit_ei_weights,
)
from packs.loader import load_pack
from schemas.engagement import EngagementEvent

PACK = load_pack("india")


def _event(channel, depth, day_offset=0) -> EngagementEvent:
    return EngagementEvent(
        brand_id=uuid4(),
        hcp_id=uuid4(),
        channel=channel,
        depth=depth,
        occurred_at=date(2026, 1, 1) + timedelta(days=day_offset),
        period="2026-01",
    )


def test_compute_ei_components_no_events_is_all_zero():
    components = compute_ei_components([], channels_offered=3, period_weeks=4, pack=PACK)
    assert components.channel_reach_ratio == 0.0
    assert components.mean_depth == 0.0
    assert components.active_week_ratio == 0.0


def test_compute_ei_components_counts_distinct_channels_and_weeks():
    events = [
        _event("rep_visit", "opened", day_offset=0),
        _event("rep_visit", "clicked", day_offset=1),  # same channel, same week
        _event("whatsapp", "attended", day_offset=8),  # different channel, different week
    ]
    components = compute_ei_components(events, channels_offered=4, period_weeks=4, pack=PACK)
    assert components.channel_reach_ratio == pytest.approx(2 / 4)
    expected_mean_depth = (PACK.engagement_depth["opened"] + PACK.engagement_depth["clicked"] + PACK.engagement_depth["attended"]) / 3
    assert components.mean_depth == pytest.approx(expected_mean_depth)
    assert components.active_week_ratio == pytest.approx(2 / 4)


def test_compute_ei_components_ratios_are_capped_at_one():
    events = [_event(f"c{i}", "attended", day_offset=i * 8) for i in range(10)]
    components = compute_ei_components(events, channels_offered=2, period_weeks=2, pack=PACK)
    assert components.channel_reach_ratio == 1.0
    assert components.active_week_ratio == 1.0


def test_compute_ei_components_rejects_nonpositive_denominators():
    with pytest.raises(ValueError):
        compute_ei_components([], channels_offered=0, period_weeks=4, pack=PACK)
    with pytest.raises(ValueError):
        compute_ei_components([], channels_offered=3, period_weeks=0, pack=PACK)


def test_compute_ei_is_zero_at_zero_components_and_100_at_full_components():
    zero = EIComponents(0.0, 0.0, 0.0)
    full = EIComponents(1.0, 1.0, 1.0)
    assert compute_ei(zero) == 0.0
    assert compute_ei(full) == pytest.approx(100.0)


def test_compute_ei_uses_default_weights_when_none_given():
    components = EIComponents(0.6, 0.4, 0.2)
    expected = 100 * sum(DEFAULT_EI_WEIGHTS[k] * v for k, v in zip(["w_b", "w_d", "w_c"], [0.6, 0.4, 0.2]))
    assert compute_ei(components) == pytest.approx(expected)


def test_fit_ei_weights_falls_back_to_default_under_min_samples():
    samples = [(EIComponents(0.5, 0.5, 0.5), True)] * 5
    assert fit_ei_weights(samples) == DEFAULT_EI_WEIGHTS


def test_fit_ei_weights_falls_back_to_default_when_single_class():
    samples = [(EIComponents(0.5, 0.5, 0.5), True)] * (MIN_SAMPLES_FOR_WEIGHT_FIT + 5)
    assert fit_ei_weights(samples) == DEFAULT_EI_WEIGHTS


def test_fit_ei_weights_recovers_positive_weights_on_correlated_synthetic_data():
    rng = np.random.default_rng(3)
    samples = []
    for _ in range(3000):
        b, d, c = rng.uniform(0, 1, size=3)
        # moved up more often when engagement components are higher, plus noise
        p_move = 0.05 + 0.6 * (0.4 * b + 0.4 * d + 0.2 * c)
        moved = rng.uniform() < p_move
        samples.append((EIComponents(b, d, c), moved))

    weights = fit_ei_weights(samples)
    assert set(weights) == {"w_b", "w_d", "w_c"}
    assert all(w >= 0 for w in weights.values())
    assert sum(weights.values()) == pytest.approx(1.0)
    # every component genuinely drives the outcome, so no weight should collapse to zero
    assert all(w > 0.01 for w in weights.values())
