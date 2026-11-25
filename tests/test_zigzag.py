from datetime import timedelta

from alerting.checks.zigzag import check_zigzag, count_turns, newest_run
from alerting.models import Data
from tests.helpers import START, forecasts, settings

SMOOTH = [0.0, 100.0, 300.0, 500.0, 520.0, 400.0, 200.0, 0.0]
ZIGZAG = [0.0, 300.0, 100.0, 400.0, 150.0, 500.0, 200.0, 0.0]


def data(values: list[float]) -> Data:
    return Data(observed=[], forecasts={}, latest_forecast=forecasts(values))


def test_smooth_day_turns_once() -> None:
    assert count_turns(SMOOTH, min_step=20) == 1


def test_zigzag_turns_many_times() -> None:
    assert count_turns(ZIGZAG, min_step=20) == 5


def test_small_moves_are_ignored() -> None:
    assert count_turns([500.0, 510.0, 495.0, 505.0, 500.0], min_step=20) == 0


def test_small_moves_that_add_up_count() -> None:
    # Up 60 in steps of 15, then down 60 in steps of 15
    values = [0.0, 15.0, 30.0, 45.0, 60.0, 45.0, 30.0, 15.0, 0.0]
    assert count_turns(values, min_step=20) == 1


def test_flat_series_has_no_turns() -> None:
    assert count_turns([0.0] * 5, min_step=0) == 0


def test_newest_run_drops_older_forecasts() -> None:
    old = forecasts([1.0, 2.0], made_at=START)
    new = forecasts([3.0, 4.0], made_at=START + timedelta(minutes=30))
    assert newest_run([old[0], new[1]]) == [new[1]]


def test_smooth_forecast_passes() -> None:
    [result] = check_zigzag(data(SMOOTH), settings())
    assert result.passed


def test_zigzag_forecast_fails() -> None:
    [result] = check_zigzag(data(ZIGZAG), settings())
    assert not result.passed
    assert "changes of direction: 5 (limit 1)" in result.message


def test_no_forecast_fails() -> None:
    [result] = check_zigzag(data([]), settings())
    assert not result.passed
