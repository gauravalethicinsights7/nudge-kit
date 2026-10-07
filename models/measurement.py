"""Deterministic/statistical math for M8 (specs/m8-measurement.md).

    EI_i = 100 * (w_b * channels_engaged/channels_offered + w_d * mean(depth) + w_c * active_weeks/weeks)

Per CLAUDE.md rule 1, every function here is a tested pure function — no LLM
calls anywhere in this module.

No EI weights (w_b/w_d/w_c) are defined in either pack — the spec's own
Done-when ("weight re-fit to predict next-period rung movement") implies
they're *fit*, not fixed constants. `fit_ei_weights` fits them via logistic
regression against real rung-movement outcomes when enough labelled
HCP-periods exist; otherwise DEFAULT_EI_WEIGHTS (equal weight, documented,
not fabricated) is used.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression

from schemas.brand_plan import Forecast
from schemas.engagement import EngagementEvent
from schemas.measurement import AssumptionCheck
from schemas.pack import Pack

DEFAULT_EI_WEIGHTS = {"w_b": 1 / 3, "w_d": 1 / 3, "w_c": 1 / 3}
MIN_SAMPLES_FOR_WEIGHT_FIT = 30


@dataclass
class EIComponents:
    channel_reach_ratio: float  # channels_engaged / channels_offered
    mean_depth: float  # mean(pack.engagement_depth[event.depth]) over the period
    active_week_ratio: float  # distinct weeks with >=1 event / period_weeks


def compute_ei_components(
    events: list[EngagementEvent], channels_offered: int, period_weeks: int, pack: Pack
) -> EIComponents:
    if channels_offered <= 0:
        raise ValueError(f"channels_offered must be > 0, got {channels_offered}")
    if period_weeks <= 0:
        raise ValueError(f"period_weeks must be > 0, got {period_weeks}")

    channels_engaged = len({e.channel for e in events})
    channel_reach_ratio = min(channels_engaged / channels_offered, 1.0)

    depths = [pack.engagement_depth.get(e.depth, 0.0) for e in events]
    mean_depth = sum(depths) / len(depths) if depths else 0.0

    active_weeks = len({e.occurred_at.isocalendar()[1] for e in events})
    active_week_ratio = min(active_weeks / period_weeks, 1.0)

    return EIComponents(channel_reach_ratio, mean_depth, active_week_ratio)


def compute_ei(components: EIComponents, weights: dict[str, float] | None = None) -> float:
    weights = weights or DEFAULT_EI_WEIGHTS
    raw = 100.0 * (
        weights["w_b"] * components.channel_reach_ratio
        + weights["w_d"] * components.mean_depth
        + weights["w_c"] * components.active_week_ratio
    )
    return max(0.0, min(100.0, raw))


def fit_ei_weights(samples: list[tuple[EIComponents, bool]]) -> dict[str, float]:
    """Logistic regression of next-period rung movement on the three EI
    components; coefficients clipped >=0 (a negative weight on an engagement
    signal isn't a meaningful EI weight) and normalized to sum to 1. Falls
    back to DEFAULT_EI_WEIGHTS when there isn't enough labelled history, or
    when every sample has the same outcome (logistic regression can't fit a
    single class)."""
    labels = [moved_up for _, moved_up in samples]
    if len(samples) < MIN_SAMPLES_FOR_WEIGHT_FIT or len(set(labels)) < 2:
        return dict(DEFAULT_EI_WEIGHTS)

    x = np.array([[c.channel_reach_ratio, c.mean_depth, c.active_week_ratio] for c, _ in samples])
    y = np.array([1 if moved else 0 for moved in labels])

    # fit_intercept=True: real HCP populations have a nonzero baseline
    # move-up rate even at EI=0, and forcing the boundary through the origin
    # (fit_intercept=False) badly distorts the *feature* coefficients to
    # compensate — the intercept itself isn't part of the EI weights, so it's
    # fit and then discarded, not folded into w_b/w_d/w_c.
    model = LogisticRegression(fit_intercept=True)
    model.fit(x, y)
    coefs = np.clip(model.coef_[0], 0.0, None)
    total = coefs.sum()
    if total <= 0:
        return dict(DEFAULT_EI_WEIGHTS)

    normalized = coefs / total
    return {"w_b": float(normalized[0]), "w_d": float(normalized[1]), "w_c": float(normalized[2])}


def rung_transition_posterior(
    prior_p: float, pseudo_count: float, successes: int, trials: int
) -> tuple[float, float, float]:
    """Beta-Bernoulli conjugate update: the pack's single prior probability
    is converted into a Beta(alpha0, beta0) via a pseudo-count (the
    'strength' of the prior belief, in equivalent observations — a documented
    modelling choice, not a market fact). Returns (alpha, beta, posterior_mean)."""
    if trials < successes or successes < 0:
        raise ValueError(f"invalid successes={successes} for trials={trials}")
    alpha0 = prior_p * pseudo_count
    beta0 = (1 - prior_p) * pseudo_count
    alpha = alpha0 + successes
    beta = beta0 + (trials - successes)
    return alpha, beta, alpha / (alpha + beta)


def review_assumptions(
    forecast: Forecast, actual_values: dict[str, float], tolerance: float = 0.3
) -> list[AssumptionCheck]:
    """Compares each named forecast assumption (plus the overall delta_nrx
    outcome) against a caller-supplied actual, when one exists. Never
    fabricates an 'actual' for an assumption nothing measured — those are
    simply skipped, not guessed."""
    planned_by_name = {a.name: a.value for a in forecast.base.assumptions}
    planned_by_name["delta_nrx"] = forecast.base.delta_nrx

    checks = []
    for name, planned in planned_by_name.items():
        if name not in actual_values:
            continue
        actual = actual_values[name]
        held = actual == 0 if planned == 0 else abs(actual - planned) / abs(planned) <= tolerance
        checks.append(AssumptionCheck(assumption=name, held=held, planned_value=planned, actual_value=actual))
    return checks
