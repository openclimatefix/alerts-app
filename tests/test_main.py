import asyncio
from collections.abc import Sequence
from datetime import timedelta

from alerting.main import run
from alerting.models import CheckResult
from tests.helpers import START, FakeSource, forecasts, observations, settings

NOW = START + timedelta(hours=24)
DAY = [0.0, 100.0, 300.0, 500.0, 520.0, 400.0, 200.0, 0.0]
NEXT_HOURS = forecasts(DAY, start=NOW, made_at=NOW)


class FakeNotifier:
    """A notifier that keeps the results it is sent."""

    def __init__(self) -> None:
        self.sent: list[CheckResult] = []

    async def notify(self, results: Sequence[CheckResult]) -> None:
        self.sent.extend(results)


def run_all(source: FakeSource) -> list[CheckResult]:
    notifier = FakeNotifier()
    results = asyncio.run(run(source, notifier, settings(), NOW))
    assert notifier.sent == results
    return results


def test_good_forecast_passes_every_check() -> None:
    source = FakeSource({60: forecasts(DAY), 120: forecasts(DAY), 0: NEXT_HOURS}, observations(DAY))
    results = run_all(source)
    assert [r.name for r in results] == ["big_error_60min", "big_error_120min", "zigzag"]
    assert all(r.passed for r in results)
    assert [horizon for horizon, _, _ in source.requests] == [60, 120, 0]


def test_big_error_fails() -> None:
    bad = forecasts([0.0, 100.0, 300.0, 700.0, 520.0, 400.0, 200.0, 0.0])
    source = FakeSource({60: bad, 120: forecasts(DAY), 0: NEXT_HOURS}, observations(DAY))
    assert [r.passed for r in run_all(source)] == [False, True, True]


def test_no_data_fails_every_check() -> None:
    results = run_all(FakeSource())
    assert len(results) == 3
    assert not any(r.passed for r in results)
