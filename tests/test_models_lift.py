"""specs/m8-measurement.md Done-when: 'DiD recovers a planted effect in
synthetic data within CI.'
"""

import numpy as np
import pytest

from models.lift import counterfactual_trend, diff_in_differences


def test_diff_in_differences_recovers_a_planted_effect_within_ci():
    rng = np.random.default_rng(11)
    planted_effect = 5.0
    n = 100

    # both arms drift by a common secular trend (+2.0); only the test arm
    # additionally gets the planted treatment effect
    control_deltas = 2.0 + rng.normal(0, 1.0, size=n)
    test_deltas = 2.0 + planted_effect + rng.normal(0, 1.0, size=n)

    result = diff_in_differences(list(test_deltas), list(control_deltas))
    assert result.method == "did"
    assert result.ci_low <= planted_effect <= result.ci_high
    assert result.effect == pytest.approx(planted_effect, abs=1.0)


def test_diff_in_differences_ci_narrows_with_more_units():
    rng = np.random.default_rng(5)

    def deltas(n):
        return list(2.0 + rng.normal(0, 1.0, size=n)), list(2.0 + 5.0 + rng.normal(0, 1.0, size=n))

    control_small, test_small = deltas(10)
    control_large, test_large = deltas(1000)

    small = diff_in_differences(test_small, control_small)
    large = diff_in_differences(test_large, control_large)
    assert (large.ci_high - large.ci_low) < (small.ci_high - small.ci_low)


def test_diff_in_differences_requires_at_least_two_units_per_arm():
    with pytest.raises(ValueError):
        diff_in_differences([1.0], [1.0, 2.0])


def test_counterfactual_trend_recovers_a_planted_shift_within_ci():
    rng = np.random.default_rng(42)
    pre = [10.0 + 0.5 * t + rng.normal(0, 0.3) for t in range(24)]
    planted_shift = 8.0
    post = [10.0 + 0.5 * (24 + t) + planted_shift + rng.normal(0, 0.3) for t in range(6)]

    result = counterfactual_trend(pre, post)
    assert result.method == "counterfactual_trend"
    assert result.ci_low <= planted_shift <= result.ci_high
    assert result.effect == pytest.approx(planted_shift, abs=1.5)


def test_counterfactual_trend_near_zero_effect_when_post_follows_the_trend():
    pre = [10.0 + 0.5 * t for t in range(24)]
    post = [10.0 + 0.5 * (24 + t) for t in range(6)]  # exactly on-trend, no shift
    result = counterfactual_trend(pre, post)
    assert result.effect == pytest.approx(0.0, abs=1e-6)


def test_counterfactual_trend_requires_enough_pre_period_points():
    with pytest.raises(ValueError):
        counterfactual_trend([1.0, 2.0], [3.0])
    with pytest.raises(ValueError):
        counterfactual_trend([1.0, 2.0, 3.0], [])
