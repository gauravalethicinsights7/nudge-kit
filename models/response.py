"""Deterministic adstock + Hill-response math for M6 (specs/m6-channel-mix.md).
Pure functions — no pymc needed just to evaluate a curve at known parameters;
models/fitting.py is where parameters get estimated from data.
"""

from __future__ import annotations


def adstock(x: list[float], lam: float) -> list[float]:
    """A_t = x_t + lambda * A_{t-1}."""
    if not 0.0 <= lam < 1.0:
        raise ValueError(f"adstock decay lambda must be in [0, 1), got {lam}")
    result: list[float] = []
    carry = 0.0
    for value in x:
        carry = value + lam * carry
        result.append(carry)
    return result


def hill_response(a: float, alpha: float, gamma: float, beta: float) -> float:
    """R_c(A) = beta * A^alpha / (A^alpha + gamma^alpha). Monotonic increasing,
    concave for alpha<=1, S-shaped for alpha>1; saturates at beta as A -> inf."""
    if a <= 0:
        return 0.0
    a_pow = a**alpha
    gamma_pow = gamma**alpha
    return beta * a_pow / (a_pow + gamma_pow)


def marginal_response(a: float, alpha: float, gamma: float, beta: float) -> float:
    """dR/dA, closed form: beta * alpha * gamma^alpha * A^(alpha-1) / (A^alpha + gamma^alpha)^2."""
    if a <= 0:
        return 0.0
    a_pow = a**alpha
    gamma_pow = gamma**alpha
    denom = (a_pow + gamma_pow) ** 2
    return beta * alpha * gamma_pow * (a ** (alpha - 1)) / denom


def curve_position(a: float, gamma: float) -> str:
    """under / efficient / saturated, by comparing adstocked activity A to the
    curve's half-saturation point gamma — a simple, defensible positioning
    heuristic (A << gamma: under-invested; A >> gamma: saturated)."""
    if gamma <= 0:
        return "efficient"
    ratio = a / gamma
    if ratio < 0.5:
        return "under"
    if ratio > 2.0:
        return "saturated"
    return "efficient"
