"""Bayesian adstock+Hill curve fitting for M6 (specs/m6-channel-mix.md), built
on plain pymc rather than pymc-marketing — see pyproject.toml's comment for
why pymc-marketing itself is unusable in this environment (a confirmed
pydantic 2.13 incompatibility in its transformer classes).

A second, unrelated environment issue: pytensor's default C++ backend fails to
link on this machine (`ld: library 'd64' not found` — a macOS toolchain
issue), and its numba fallback also fails (numba/numpy version mismatch).
Forcing the plain-Python pytensor linker works, just slower (no JIT/C) — fine
for this module's scale (one channel's curve, <=60 periods of history).

Falls back to the pack's own curve_prior when there isn't enough history
(spec: '>= 24 periods... else pack priors, confidence <= 0.4').
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytensor

# See module docstring: this environment's pytensor C/numba backends are both
# broken; the plain-Python linker is the one that actually works here. cxx
# must ALSO be cleared, or pytensor still tries (and fails) to compile its
# internal lazylinker_ext helper on first use, regardless of config.linker.
pytensor.config.linker = "py"
pytensor.config.cxx = ""

import arviz as az  # noqa: E402
import pymc as pm  # noqa: E402
import pytensor.tensor as pt  # noqa: E402

from schemas.channel import ResponseCurve  # noqa: E402
from schemas.enums import CurveSource  # noqa: E402

MIN_PERIODS_FOR_FITTING = 24  # spec: ">= 24 periods of history"
PRIOR_CONFIDENCE_CAP = 0.4  # spec: "else use pack priors (source=prior, confidence <= 0.4)"


def _adstock_matrix(t: int, lam) -> "pt.TensorVariable":
    """A = L @ x where L[i,j] = lam^(i-j) for i>=j, else 0 — a closed-form,
    scan-free way to express the recursive adstock filter A_t = x_t + lam*A_{t-1}
    as a single differentiable matrix op pymc can sample through."""
    idx = np.arange(t)
    diff = idx[:, None] - idx[None, :]
    mask = diff >= 0
    diff_clipped = np.clip(diff, 0, None)
    return pt.where(mask, lam**diff_clipped, 0.0)


def fit_response_curve(
    history: pd.DataFrame | None,
    prior: ResponseCurve,
    draws: int = 600,
    tune: int = 600,
    chains: int = 2,
    seed: int = 42,
) -> tuple[ResponseCurve, dict]:
    """history: columns 'activity' (spend/units) and 'outcome' (response),
    one row per period, in period order. Returns (curve, diagnostics);
    diagnostics is {} for the prior fallback (nothing to report)."""
    if history is None or len(history) < MIN_PERIODS_FOR_FITTING:
        return prior, {}

    x = history["activity"].to_numpy(dtype=float)
    y = history["outcome"].to_numpy(dtype=float)
    t = len(x)

    with pm.Model():
        lam = pm.Beta("lam", alpha=2, beta=2)
        alpha = pm.Gamma("alpha", alpha=3, beta=2)
        gamma = pm.HalfNormal("gamma", sigma=max(float(x.mean()), 1.0) * 3)
        beta = pm.HalfNormal("beta", sigma=max(float(y.max()), 1.0) * 3)
        sigma = pm.HalfNormal("sigma", sigma=max(float(y.std()), 1.0))

        adstock_matrix = _adstock_matrix(t, lam)
        a_seq = pt.dot(adstock_matrix, x)

        mu = beta * (a_seq**alpha) / (a_seq**alpha + gamma**alpha)
        pm.Normal("obs", mu=mu, sigma=sigma, observed=y)

        idata = pm.sample(draws=draws, tune=tune, chains=chains, random_seed=seed, progressbar=False)

    summary = az.summary(idata, var_names=["lam", "alpha", "gamma", "beta"])
    fitted = ResponseCurve.model_validate(
        {
            "lambda": float(summary.loc["lam", "mean"]),
            "alpha": float(summary.loc["alpha", "mean"]),
            "gamma": float(summary.loc["gamma", "mean"]),
            "beta": float(summary.loc["beta", "mean"]),
            "source": CurveSource.fitted,
        }
    )
    diagnostics = {
        "periods_used": t,
        "r_hat_max": float(summary["r_hat"].max()),
        "ess_bulk_min": float(summary["ess_bulk"].min()),
    }
    return fitted, diagnostics
