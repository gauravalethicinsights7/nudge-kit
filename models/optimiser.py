"""Budget optimiser for M6 (specs/m6-channel-mix.md):
max sum_c fit_c * R_c(x_c)  s.t. sum spend <= budget; capacity; freq_cap; compliance.

The spec frames this as "concave response -> convex problem" for cvxpy. That
holds only when every channel's Hill exponent alpha <= 1 — but most channels
in both shipped packs have alpha > 1 (rep_visit=1.5, kol_peer=1.5,
webinar_cme=1.3, etc. — S-shaped, not concave), which is not DCP-representable
as a clean convex maximization. Rather than force a cvxpy formulation that
doesn't apply to the actual pack data, this uses scipy's SLSQP (general
nonlinear constrained optimization, handles both shapes) as the one real,
tested solver — the spec's own fallback option, just promoted to primary
given what the real curves look like. cvxpy stays a project dependency for
when a genuinely concave (alpha<=1) case is worth a dedicated DCP path.

Adstock is treated at steady state: a constant monthly activity level x_c
carries over as A_c = x_c / (1 - lambda_c) (the geometric-series steady
state of A_t = x_t + lambda*A_{t-1} when x_t is constant) — the right
simplification for a monthly touches_per_month allocation, as opposed to a
full dynamic time-series optimization.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from models.response import curve_position, hill_response, marginal_response
from schemas.channel import Channel


@dataclass
class ChannelAllocationResult:
    channel_id: str
    activity: float
    spend: float
    response: float
    marginal_roi: float
    position: str


def _steady_state_adstock(activity: float, lam: float) -> float:
    return activity / (1 - lam) if lam < 1 else activity


def optimise_mix(
    channels: list[Channel],
    fit_scores: dict[str, float],
    budget: float,
    hcp_count: float,
    freq_caps: dict[str, float] | None = None,
    compliance_allowed: dict[str, bool] | None = None,
) -> list[ChannelAllocationResult]:
    """One segment's channel mix. `freq_caps` (per pack.yaml, touches/HCP/month)
    and `hcp_count` bound each channel's activity from above; a channel with
    compliance_allowed[c]=False is fixed at zero, never allocated to — spec
    rule: 'never allocate to a channel whose compliance rules forbid it.'"""
    freq_caps = freq_caps or {}
    compliance_allowed = compliance_allowed or {}

    usable = [c for c in channels if compliance_allowed.get(c.channel_ref, True)]
    if not usable:
        return []

    unit_costs = [c.unit_cost.value if c.unit_cost else 1.0 for c in usable]
    fits = [fit_scores.get(c.channel_ref, 0.0) for c in usable]

    def response_for(spend: np.ndarray) -> np.ndarray:
        activity = spend / np.array(unit_costs)
        adstocked = np.array(
            [_steady_state_adstock(a, c.curve.lambda_) for a, c in zip(activity, usable)]
        )
        return np.array(
            [
                hill_response(a, c.curve.alpha, c.curve.gamma, c.curve.beta or 1.0)
                for a, c in zip(adstocked, usable)
            ]
        )

    def negative_objective(spend: np.ndarray) -> float:
        return -float(np.dot(fits, response_for(spend)))

    n = len(usable)
    upper_bounds = []
    for c, unit_cost in zip(usable, unit_costs):
        bound = budget
        if c.capacity is not None:
            bound = min(bound, c.capacity * unit_cost)
        cap = freq_caps.get(c.channel_ref)
        if cap is not None:
            bound = min(bound, cap * hcp_count * unit_cost)
        upper_bounds.append(max(bound, 0.0))

    bounds = [(0.0, ub) for ub in upper_bounds]
    constraints = [{"type": "ineq", "fun": lambda spend: budget - np.sum(spend)}]

    if n == 0 or budget <= 0:
        spends = np.zeros(n)
    else:
        # Most real pack curves have alpha>1 (S-shaped, non-concave — see
        # module docstring), so SLSQP's local search can converge to a
        # materially inferior local optimum depending on where it starts
        # (confirmed by tests/test_models_backtest.py once: a single
        # equal-split start underperformed a naive equal-split baseline on
        # held-out periods). Multi-start with a handful of structurally
        # different starting points and keeping the best fixes this cheaply.
        starting_points = [np.array([min(ub, budget / n) for ub in upper_bounds])]
        for favored in range(n):
            x0 = np.zeros(n)
            x0[favored] = min(upper_bounds[favored], budget)
            remaining = budget - x0[favored]
            others = [i for i in range(n) if i != favored]
            if remaining > 0 and others:
                share = remaining / len(others)
                for i in others:
                    x0[i] = min(upper_bounds[i], share)
            starting_points.append(x0)

        best_spends = None
        best_value = float("inf")
        for x0 in starting_points:
            result = minimize(
                negative_objective, x0, method="SLSQP", bounds=bounds, constraints=constraints,
                options={"maxiter": 200, "ftol": 1e-9},
            )
            candidate = np.clip(result.x, 0, None)
            total = candidate.sum()
            if total > budget > 0:
                candidate = candidate * (budget / total)
            value = negative_objective(candidate)
            if value < best_value:
                best_value = value
                best_spends = candidate
        spends = best_spends

    allocations = []
    for channel, spend, unit_cost, fit in zip(usable, spends, unit_costs, fits):
        activity = spend / unit_cost
        adstocked = _steady_state_adstock(activity, channel.curve.lambda_)
        response = hill_response(adstocked, channel.curve.alpha, channel.curve.gamma, channel.curve.beta or 1.0)
        marginal = (
            fit
            * marginal_response(adstocked, channel.curve.alpha, channel.curve.gamma, channel.curve.beta or 1.0)
            / (1 - channel.curve.lambda_)
            / unit_cost
            if channel.curve.lambda_ < 1
            else 0.0
        )
        allocations.append(
            ChannelAllocationResult(
                channel_id=channel.channel_ref,
                activity=float(activity),
                spend=float(spend),
                response=float(response),
                marginal_roi=float(marginal),
                position=curve_position(adstocked, channel.curve.gamma),
            )
        )

    for channel in channels:
        if channel.channel_ref not in {a.channel_id for a in allocations}:
            allocations.append(
                ChannelAllocationResult(
                    channel_id=channel.channel_ref, activity=0.0, spend=0.0, response=0.0,
                    marginal_roi=0.0, position="under",
                )
            )

    return allocations
