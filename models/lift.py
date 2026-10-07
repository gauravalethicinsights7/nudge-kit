"""Causal lift estimation for M8 (specs/m8-measurement.md):
    lift: difference-in-differences on matched test/control (territory or HCP
    cohorts); CausalImpact-style fallback for national.

No CausalImpact/BSTS library is installed in this project (not in
pyproject.toml, and adding a heavy new dependency for one fallback path is
out of scope for this session). `counterfactual_trend` is a real, simplified,
testable stand-in — an OLS trend fit on the pre-period series, projected
forward, with a residual-based prediction interval — not the actual
CausalImpact algorithm. Documented here, not hidden.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

Z_95 = 1.959963984540054  # scipy.stats.norm.ppf(0.975)


@dataclass
class LiftResult:
    effect: float
    ci_low: float
    ci_high: float
    method: str


def diff_in_differences(test_deltas: list[float], control_deltas: list[float]) -> LiftResult:
    """test_deltas/control_deltas: per-unit (HCP or territory) post-minus-pre
    outcome changes for the treated and matched-control cohorts. effect =
    mean(test_deltas) - mean(control_deltas); CI via the standard combined-
    variance normal approximation for a difference of two sample means."""
    if len(test_deltas) < 2 or len(control_deltas) < 2:
        raise ValueError("need at least 2 units per arm to estimate a variance")

    test_arr, control_arr = np.array(test_deltas), np.array(control_deltas)
    effect = float(test_arr.mean() - control_arr.mean())
    se = math.sqrt(test_arr.var(ddof=1) / len(test_arr) + control_arr.var(ddof=1) / len(control_arr))
    return LiftResult(effect=effect, ci_low=effect - Z_95 * se, ci_high=effect + Z_95 * se, method="did")


def counterfactual_trend(pre_values: list[float], post_values: list[float]) -> LiftResult:
    """CausalImpact-style stand-in (see module docstring): fits an OLS line
    to the pre-period series, projects it across the post period, and takes
    actual-minus-predicted as the effect. The prediction interval comes from
    the pre-period fit's own residual standard deviation."""
    if len(pre_values) < 3:
        raise ValueError("need at least 3 pre-period points to fit a trend")
    if not post_values:
        raise ValueError("need at least 1 post-period point")

    pre_t = np.arange(len(pre_values))
    slope, intercept = np.polyfit(pre_t, pre_values, 1)
    fitted = slope * pre_t + intercept
    residual_std = float(np.std(np.array(pre_values) - fitted, ddof=1)) if len(pre_values) > 2 else 0.0

    post_t = np.arange(len(pre_values), len(pre_values) + len(post_values))
    predicted = slope * post_t + intercept
    effect = float(np.mean(np.array(post_values) - predicted))

    se = residual_std / math.sqrt(len(post_values)) if residual_std > 0 else 0.0
    return LiftResult(
        effect=effect, ci_low=effect - Z_95 * se, ci_high=effect + Z_95 * se, method="counterfactual_trend"
    )
