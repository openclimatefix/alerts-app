import asyncio
from datetime import timedelta

from alerting.checks.big_errors import biggest_error, check_big_errors, error_pct, pair
from alerting.config import CheckSettings
from alerting.models import CheckResult
from tests.helpers import START, FakeSource, forecasts, observations, settings

NOW = START + timedelta(hours=12)


def check(
    forecast_mw: list[float], observed_mw: list[float], config: CheckSettings | None = None
) -> list[CheckResult]:
    config = config or settings(horizons_mins=[60])
    source = FakeSource({60: forecasts(forecast_mw)}, observations(observed_mw))
    return asyncio.run(check_big_errors(source, config, NOW))


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
    [result] = check([100.0, 220.0, 300.0], [110.0, 200.0, 290.0])
    assert result.passed


def test_one_big_error_fails() -> None:
    # Spot on 20 times, then 150 MW out once. The MAE is only 7 MW.
    [result] = check([0.0] * 20 + [650.0], [0.0] * 20 + [500.0])
    assert not result.passed
    assert "biggest error 150 MW (15.0% of capacity, limit 10%)" in result.message
    assert "MAE 7 MW" in result.message


def test_error_on_the_limit_passes() -> None:
    [result] = check([600.0], [500.0])
    assert result.passed


def test_no_matching_times_fails() -> None:
    [result] = check([100.0], [])
    assert not result.passed


def test_one_result_per_horizon() -> None:
    results = check([100.0], [100.0], settings(horizons_mins=[60, 120]))
    assert [result.name for result in results] == ["big_error_60min", "big_error_120min"]


def test_asks_for_the_window_before_now() -> None:
    source = FakeSource()
    asyncio.run(check_big_errors(source, settings(horizons_mins=[60], window_hours=6), NOW))
    assert source.requests == [(60, NOW - timedelta(hours=6), NOW)]


def test_data_outside_the_window_is_not_checked() -> None:
    # 900 MW out a day before the window starts
    day_before = START - timedelta(hours=24)
    source = FakeSource(
        {60: forecasts([900.0], start=day_before) + forecasts([100.0])},
        observations([0.0], start=day_before) + observations([100.0]),
    )
    [result] = asyncio.run(check_big_errors(source, settings(horizons_mins=[60]), NOW))
    assert result.passed
