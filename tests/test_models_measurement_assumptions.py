from datetime import date

from models.measurement import review_assumptions
from schemas.base import Origin, ProvMoney
from schemas.brand_plan import Forecast, ForecastAssumption, ForecastScenario


def _forecast() -> Forecast:
    revenue = ProvMoney(value=1_000_000.0, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5, currency="INR")
    base = ForecastScenario(
        delta_nrx=100.0,
        revenue=revenue,
        assumptions=[
            ForecastAssumption(name="persistence", value=1.0, confidence=0.3),
            ForecastAssumption(name="net_price", value=5000.0, confidence=0.8),
        ],
    )
    return Forecast(base=base, upside=base, downside=base)


def test_review_assumptions_flags_held_within_tolerance():
    checks = review_assumptions(_forecast(), actual_values={"delta_nrx": 105.0}, tolerance=0.1)
    assert len(checks) == 1
    assert checks[0].assumption == "delta_nrx"
    assert checks[0].held is True


def test_review_assumptions_flags_failed_outside_tolerance():
    checks = review_assumptions(_forecast(), actual_values={"delta_nrx": 50.0}, tolerance=0.1)
    assert checks[0].held is False


def test_review_assumptions_skips_names_without_an_actual():
    checks = review_assumptions(_forecast(), actual_values={"net_price": 5000.0})
    names = {c.assumption for c in checks}
    assert names == {"net_price"}
    assert "persistence" not in names
    assert "delta_nrx" not in names


def test_review_assumptions_handles_zero_planned_value():
    forecast = _forecast()
    forecast.base.delta_nrx = 0.0
    held_checks = review_assumptions(forecast, actual_values={"delta_nrx": 0.0})
    failed_checks = review_assumptions(forecast, actual_values={"delta_nrx": 5.0})
    assert held_checks[0].held is True
    assert failed_checks[0].held is False


def test_review_assumptions_checks_multiple_named_assumptions_independently():
    checks = review_assumptions(
        _forecast(), actual_values={"persistence": 1.0, "net_price": 10000.0}, tolerance=0.1
    )
    by_name = {c.assumption: c.held for c in checks}
    assert by_name["persistence"] is True
    assert by_name["net_price"] is False
