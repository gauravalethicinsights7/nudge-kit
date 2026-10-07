"""Gate 3 backtest (specs/m6-channel-mix.md's last Done-when item:
"Recommended mix beats current mix on held-out synthetic periods"). Plays a
fixed monthly spend allocation forward through the real adstock recursion
(models.response.adstock) across a run of synthetic held-out periods and
sums the fit-weighted response — this is what proves the optimiser's
recommended mix outperforms a naive baseline, separate from (and simpler
than) models/fitting.py's own PyMC parameter-recovery backtest (the spec's
"fitted params recover truth" bullet, covered by tests/test_models_fitting.py).
"""

from __future__ import annotations

from dataclasses import dataclass

from models.response import adstock, hill_response
from schemas.channel import Channel


@dataclass
class BacktestResult:
    current_total_response: float
    recommended_total_response: float
    uplift: float
    uplift_pct: float | None  # None when current_total_response is 0


def _held_out_response(channel: Channel, monthly_activity: float, periods: int, fit_score: float) -> float:
    """Plays a constant monthly activity level forward through `periods`
    held-out months via the real adstock recursion, summing fit-weighted
    Hill response per period."""
    activity_series = adstock([monthly_activity] * periods, channel.curve.lambda_)
    return sum(
        fit_score * hill_response(a, channel.curve.alpha, channel.curve.gamma, channel.curve.beta or 1.0)
        for a in activity_series
    )


def backtest_recommended_vs_current(
    channels: list[Channel],
    fit_scores: dict[str, float],
    current_spend_by_channel: dict[str, float],
    recommended_spend_by_channel: dict[str, float],
    periods: int = 12,
) -> BacktestResult:
    """Compares two fixed monthly spend allocations (e.g. a naive equal split
    vs. optimise_mix's output) by playing each forward through `periods`
    held-out synthetic months against the channels' own response curves."""

    def total_for(spend_by_channel: dict[str, float]) -> float:
        total = 0.0
        for channel in channels:
            spend = spend_by_channel.get(channel.channel_ref, 0.0)
            unit_cost = channel.unit_cost.value if channel.unit_cost else 1.0
            activity = spend / unit_cost if unit_cost else 0.0
            total += _held_out_response(channel, activity, periods, fit_scores.get(channel.channel_ref, 0.0))
        return total

    current_total = total_for(current_spend_by_channel)
    recommended_total = total_for(recommended_spend_by_channel)
    uplift = recommended_total - current_total
    uplift_pct = (uplift / current_total) if current_total > 0 else None
    return BacktestResult(current_total, recommended_total, uplift, uplift_pct)
