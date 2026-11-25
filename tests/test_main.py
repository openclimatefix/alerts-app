import asyncio
from datetime import datetime, timedelta

from alerting.main import load_data, report, run_checks
from alerting.models import CheckResult, Forecast, Observation
from tests.helpers import START, forecasts, observations, settings

NOW = START + timedelta(hours=24)
DAY = [0.0, 100.0, 300.0, 500.0, 520.0, 400.0, 200.0, 0.0]
NEXT_HOURS = forecasts(DAY, start=NOW, made_at=NOW)


class FakeSource:
    """A data source that serves values from memory."""

    def __init__(self, forecast: list[Forecast], observed: list[Observation]) -> None:
        self.forecast = forecast
        self.observed = observed
        self.horizons: list[int] = []

    async def get_forecast(
        self, horizon_mins: int, start: datetime, end: datetime
    ) -> list[Forecast]:
        self.horizons.append(horizon_mins)
        return [f for f in self.forecast if start <= f.time <= end]

    async def get_observations(self, start: datetime, end: datetime) -> list[Observation]:
        return [o for o in self.observed if start <= o.time <= end]


def run(source: FakeSource) -> list[CheckResult]:
    config = settings()
    return run_checks(asyncio.run(load_data(source, config, NOW)), config)


def test_good_forecast_passes_every_check() -> None:
    source = FakeSource(forecasts(DAY) + NEXT_HOURS, observations(DAY))
    results = run(source)
    assert [r.name for r in results] == ["big_error_60min", "big_error_120min", "zigzag"]
    assert all(r.passed for r in results)
    assert source.horizons == [60, 120, 0]


def test_big_error_fails() -> None:
    forecast = forecasts([0.0, 100.0, 300.0, 700.0, 520.0, 400.0, 200.0, 0.0])
    results = run(FakeSource(forecast + NEXT_HOURS, observations(DAY)))
    assert [r.passed for r in results] == [False, False, True]


def test_no_data_fails_every_check() -> None:
    results = run(FakeSource([], []))
    assert len(results) == 3
    assert not any(r.passed for r in results)


def test_data_outside_the_window_is_not_checked() -> None:
    two_days_ago = START - timedelta(hours=24)
    old = forecasts([900.0], start=two_days_ago), observations([0.0], start=two_days_ago)
    source = FakeSource(old[0] + forecasts(DAY) + NEXT_HOURS, old[1] + observations(DAY))
    assert all(r.passed for r in run(source))


def test_report_returns_the_exit_code() -> None:
    passed = CheckResult("a", True, "fine")
    failed = CheckResult("b", False, "broken")
    assert report([passed]) == 0
    assert report([passed, failed]) == 1
