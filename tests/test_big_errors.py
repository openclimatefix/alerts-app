from datetime import timedelta

from alerting.checks.big_errors import biggest_error, check_big_errors, error_pct, pair
from alerting.models import Data
from tests.helpers import START, forecasts, observations, settings


def data(forecast_mw: list[float], observed_mw: list[float]) -> Data:
    return Data(
        observed=observations(observed_mw),
        forecasts={60: forecasts(forecast_mw)},
        latest_forecast=[],
    )


def test_pair_keeps_times_that_have_both() -> None:
    forecast = forecasts([1.0, 2.0, 3.0])
    observed = observations([5.0, 6.0], start=START + timedelta(minutes=30))
    assert [(f.mw, o.mw) for f, o in pair(forecast, observed)] == [(2.0, 5.0), (3.0, 6.0)]


def test_error_pct() -> None:
    [(forecast, observed)] = pair(forecasts([600.0]), observations([500.0]))
    assert error_pct(forecast, observed) == 10.0


def test_biggest_error() -> None:
    pairs = pair(forecasts([100.0, 300.0, 100.0]), observations([100.0, 100.0, 150.0]))
    forecast, observed = biggest_error(pairs)
    assert (forecast.mw, observed.mw) == (300.0, 100.0)


def test_small_errors_pass() -> None:
    [result] = check_big_errors(
        data([100.0, 220.0, 300.0], [110.0, 200.0, 290.0]), settings(error_limit_pct=10)
    )
    assert result.passed


def test_one_big_error_fails() -> None:
    # Spot on 20 times, then 150 MW out once. The MAE is only 7 MW.
    [result] = check_big_errors(
        data([0.0] * 20 + [650.0], [0.0] * 20 + [500.0]), settings(error_limit_pct=10)
    )
    assert not result.passed
    assert "biggest error 150 MW (15.0% of capacity, limit 10%)" in result.message
    assert "MAE 7 MW" in result.message


def test_error_on_the_limit_passes() -> None:
    [result] = check_big_errors(data([600.0], [500.0]), settings(error_limit_pct=10))
    assert result.passed


def test_no_matching_times_fails() -> None:
    [result] = check_big_errors(data([100.0], []), settings())
    assert not result.passed


def test_one_result_per_horizon() -> None:
    both = Data(
        observed=observations([100.0]),
        forecasts={60: forecasts([100.0]), 120: forecasts([100.0])},
        latest_forecast=[],
    )
    names = [result.name for result in check_big_errors(both, settings())]
    assert names == ["big_error_60min", "big_error_120min"]
