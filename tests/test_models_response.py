import pytest

from models.response import adstock, curve_position, hill_response, marginal_response


def test_adstock_recursion_matches_manual_computation():
    x = [10.0, 20.0, 0.0, 5.0]
    lam = 0.5
    result = adstock(x, lam)
    expected = []
    carry = 0.0
    for v in x:
        carry = v + lam * carry
        expected.append(carry)
    assert result == pytest.approx(expected)


def test_adstock_zero_lambda_is_identity():
    x = [1.0, 2.0, 3.0]
    assert adstock(x, 0.0) == pytest.approx(x)


def test_adstock_rejects_invalid_lambda():
    with pytest.raises(ValueError):
        adstock([1.0], 1.0)
    with pytest.raises(ValueError):
        adstock([1.0], -0.1)


def test_hill_response_zero_at_zero_activity():
    assert hill_response(0.0, alpha=1.5, gamma=10.0, beta=100.0) == 0.0


def test_hill_response_approaches_beta_at_large_activity():
    r = hill_response(1_000_000.0, alpha=1.5, gamma=10.0, beta=100.0)
    assert r == pytest.approx(100.0, rel=1e-3)


def test_hill_response_is_monotonic_increasing():
    values = [hill_response(a, alpha=1.2, gamma=20.0, beta=50.0) for a in [0, 5, 10, 20, 40, 100]]
    assert values == sorted(values)


def test_marginal_response_is_nonnegative_and_decreases_past_saturation():
    m_low = marginal_response(5.0, alpha=1.2, gamma=20.0, beta=50.0)
    m_high = marginal_response(200.0, alpha=1.2, gamma=20.0, beta=50.0)
    assert m_low >= 0
    assert m_high >= 0
    assert m_high < m_low  # diminishing marginal returns past the curve's saturation point


def test_curve_position_labels():
    assert curve_position(1.0, gamma=10.0) == "under"
    assert curve_position(10.0, gamma=10.0) == "efficient"
    assert curve_position(30.0, gamma=10.0) == "saturated"
