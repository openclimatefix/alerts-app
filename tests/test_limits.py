import logging
from datetime import timedelta

import pytest

from alerting.limits import daily_biggest_errors, report
from tests.helpers import START, forecasts, observations

NEXT_DAY = START + timedelta(days=1)
# Biggest error is 200 MW on the first day and 50 MW on the second
FORECAST = forecasts([100.0, 300.0]) + forecasts([100.0, 100.0], start=NEXT_DAY)
OBSERVED = observations([100.0, 100.0]) + observations([150.0, 100.0], start=NEXT_DAY)


def test_biggest_error_of_each_day() -> None:
    worst = daily_biggest_errors(FORECAST, OBSERVED)
    assert [(f.time, f.mw - o.mw) for f, o in worst] == [
        (START + timedelta(minutes=30), 200.0),
        (NEXT_DAY, -50.0),
    ]


def test_report_logs_the_percentiles(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    report(60, daily_biggest_errors(FORECAST, OBSERVED))

    assert "Horizon 60 min: 2 days from 2026-06-01 to 2026-06-02" in caplog.text
    # Daily biggest errors are 20% and 5% of capacity
    assert "P95 of the daily biggest error: 19.2% of capacity" in caplog.text
    assert "2026-06-01 00:30: 200 MW (20.0%), forecast made at 2026-06-01 00:00" in caplog.text
    assert "2026-06: 2 days, P95 19.2%, worst 20.0%" in caplog.text


def test_report_with_no_data(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    report(60, [])
    assert "no forecast and observation at the same times" in caplog.text
