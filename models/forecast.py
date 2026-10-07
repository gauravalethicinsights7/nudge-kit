"""Deterministic forecasting math for M5 (specs/m5-brand-plan.md).

M5's own Inputs list only includes Segment[] (not HCP[]/AdoptionState[]), so
delta_p_s,k collapses to the segment-level aggregate models/scores.py's
p_move_up already computes from pack.priors.rung_transition_monthly, keyed by
each imperative's own from_rung — reusing M2's exact function rather than
duplicating rung-transition logic. "New patients" volume reuses the same
potential*share-gap base as models/plan.py::revenue_at_stake.

margin and incremental_spend aren't in M5's inputs either (Budget is
explicitly "from M6, placeholder until run"); both are tracked, low-
confidence assumptions here, not fabricated facts. Forecasting happens at the
plan level (one base/upside/downside set), matching BrandPlan.forecast's shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from models.scores import p_move_up
from schemas.base import Origin, ProvMoney
from schemas.brand_plan import Forecast, ForecastAssumption, ForecastScenario
from schemas.enums import Rung
from schemas.hcp import Segment
from schemas.pack import Pack

# Neutral placeholders used only when no real data exists — always tracked as
# a low-confidence assumption in the output, never presented as fact.
DEFAULT_MARGIN_ASSUMPTION = 0.6
DEFAULT_MARGIN_CONFIDENCE = 0.3
DEFAULT_PERSISTENCE_ASSUMPTION = 1.0  # "assume full persistence" is the only non-fabricated neutral default
DEFAULT_PERSISTENCE_CONFIDENCE = 0.3
NET_PRICE_CONFIDENCE = 0.8  # a stated user input, not estimated


def compute_delta_nrx(segment: Segment, from_rung: Rung, pack: Pack, persistence: float) -> float:
    """delta_nrx_s = N_s * sum_k(delta_p_s,k * new_patients_s,k) * persistence_s,
    collapsed to segment-level aggregates (see module docstring)."""
    opportunity_volume = segment.total_potential * max(segment.target_share - segment.avg_share, 0.0)
    delta_p = p_move_up(from_rung, pack)
    return opportunity_volume * delta_p * persistence


def compute_revenue_and_roi(
    delta_nrx: float,
    net_price: float,
    currency: str,
    margin: float,
    incremental_spend: float | None,
    as_of: date | None = None,
) -> tuple[ProvMoney, float | None]:
    """revenue = delta_nrx * net_price; roi = (revenue*margin - incremental_spend) / incremental_spend.
    ROI is None (never fabricated) when incremental_spend isn't known."""
    as_of = as_of or date.today()
    revenue_value = delta_nrx * net_price
    revenue = ProvMoney(
        value=revenue_value,
        source="models.forecast.compute_revenue_and_roi",
        origin=Origin.estimated,
        as_of=as_of,
        confidence=0.4,
        currency=currency,
    )
    if not incremental_spend:
        return revenue, None
    roi = (revenue_value * margin - incremental_spend) / incremental_spend
    return revenue, roi


@dataclass
class SensitivityResult:
    name: str
    low_output: float
    high_output: float
    swing: float


def tornado_sensitivity(
    assumptions: dict[str, tuple[float, float]],
    compute_fn: Callable[[dict[str, float]], float],
    top_n: int = 3,
) -> list[SensitivityResult]:
    """assumptions: {name: (value, confidence)}. SD derived from confidence
    (sd_fraction = (1 - confidence) * 0.5 — lower confidence, wider swing):
    a documented convention, since no historical variance data exists
    anywhere in this build, not a measured uncertainty."""
    base_values = {name: value for name, (value, _confidence) in assumptions.items()}
    results = []

    for name, (value, confidence) in assumptions.items():
        sd_fraction = (1 - confidence) * 0.5
        low_overrides = dict(base_values, **{name: value * (1 - sd_fraction)})
        high_overrides = dict(base_values, **{name: value * (1 + sd_fraction)})
        low_output = compute_fn(low_overrides)
        high_output = compute_fn(high_overrides)
        results.append(
            SensitivityResult(
                name=name, low_output=low_output, high_output=high_output, swing=abs(high_output - low_output)
            )
        )

    results.sort(key=lambda r: r.swing, reverse=True)
    return results[:top_n]


def build_scenarios(
    segments_and_from_rungs: list[tuple[Segment, Rung]],
    pack: Pack,
    net_price: float,
    currency: str,
    budget_envelope: float | None,
    persistence: float | None = None,
    margin: float | None = None,
    as_of: date | None = None,
) -> Forecast:
    """One imperative -> (segment, from_rung) pair; delta_nrx sums across all
    of them. persistence/margin default to the neutral, low-confidence
    placeholders above when not supplied (e.g. pack.priors.persistence_6m_default
    is null in both shipped packs today)."""
    as_of = as_of or date.today()
    persistence_value = persistence if persistence is not None else DEFAULT_PERSISTENCE_ASSUMPTION
    persistence_confidence = 1.0 if persistence is not None else DEFAULT_PERSISTENCE_CONFIDENCE
    margin_value = margin if margin is not None else DEFAULT_MARGIN_ASSUMPTION
    margin_confidence = 1.0 if margin is not None else DEFAULT_MARGIN_CONFIDENCE

    def total_delta_nrx(persistence_val: float) -> float:
        return sum(
            compute_delta_nrx(segment, from_rung, pack, persistence_val)
            for segment, from_rung in segments_and_from_rungs
        )

    assumptions_for_tornado = {
        "persistence": (persistence_value, persistence_confidence),
        "margin": (margin_value, margin_confidence),
        "net_price": (net_price, NET_PRICE_CONFIDENCE),
    }

    def revenue_output(overrides: dict[str, float]) -> float:
        return total_delta_nrx(overrides["persistence"]) * overrides["net_price"]

    sensitivity = tornado_sensitivity(assumptions_for_tornado, revenue_output, top_n=3)
    scenario_assumptions = [
        ForecastAssumption(name=r.name, value=assumptions_for_tornado[r.name][0], confidence=assumptions_for_tornado[r.name][1])
        for r in sensitivity
    ]

    def scenario_for(direction: str | None) -> ForecastScenario:
        overrides = {"persistence": persistence_value, "net_price": net_price, "margin": margin_value}
        if direction is not None:
            for r in sensitivity:
                value, confidence = assumptions_for_tornado[r.name]
                sd_fraction = (1 - confidence) * 0.5
                sign = 1 if direction == "upside" else -1
                overrides[r.name] = value * (1 + sign * sd_fraction)

        delta_nrx = total_delta_nrx(overrides["persistence"])
        revenue, roi = compute_revenue_and_roi(
            delta_nrx, overrides["net_price"], currency, overrides["margin"], budget_envelope, as_of
        )
        return ForecastScenario(delta_nrx=delta_nrx, revenue=revenue, roi=roi, assumptions=scenario_assumptions)

    return Forecast(base=scenario_for(None), upside=scenario_for("upside"), downside=scenario_for("downside"))
