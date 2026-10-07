import numpy as np
import pandas as pd
import pytest

from models.fitting import fit_response_curve
from schemas.channel import ResponseCurve
from schemas.enums import CurveSource

pytestmark = pytest.mark.slow

PRIOR = ResponseCurve.model_validate(
    {"lambda": 0.3, "alpha": 1.2, "gamma": 20.0, "beta": 100.0, "source": CurveSource.prior}
)


def test_fit_response_curve_returns_prior_unchanged_when_history_too_short():
    short_history = pd.DataFrame({"activity": [10.0] * 10, "outcome": [5.0] * 10})
    curve, diagnostics = fit_response_curve(short_history, PRIOR)
    assert curve is PRIOR
    assert diagnostics == {}


def test_fit_response_curve_returns_prior_unchanged_when_history_is_none():
    curve, diagnostics = fit_response_curve(None, PRIOR)
    assert curve is PRIOR
    assert diagnostics == {}


def test_fit_response_curve_recovers_known_parameters_from_synthetic_data():
    true_lam, true_alpha, true_gamma, true_beta = 0.35, 1.3, 25.0, 100.0
    rng = np.random.default_rng(7)
    t = 36
    x = rng.uniform(5.0, 40.0, size=t)

    # replicate the model's own adstock formula to build noise-free synthetic history
    a = np.zeros(t)
    carry = 0.0
    for i in range(t):
        carry = x[i] + true_lam * carry
        a[i] = carry
    mu = true_beta * (a**true_alpha) / (a**true_alpha + true_gamma**true_alpha)
    y = mu + rng.normal(0, 1.0, size=t)

    history = pd.DataFrame({"activity": x, "outcome": y})
    curve, diagnostics = fit_response_curve(history, PRIOR, draws=300, tune=300, chains=2, seed=7)

    assert curve.source == CurveSource.fitted
    assert diagnostics["periods_used"] == t
    assert curve.lambda_ == pytest.approx(true_lam, rel=0.2, abs=0.1)
    assert curve.gamma == pytest.approx(true_gamma, rel=0.2)
    assert curve.beta == pytest.approx(true_beta, rel=0.2)
