import pytest

from alerting.checks.errors import (
    absolute_errors,
    mae,
    mean_error,
    percentile,
    rmse,
)


def test_absolute_errors() -> None:
    assert absolute_errors([1.0, 2.0, 3.0], [2.0, 2.0, 1.0]) == [1.0, 0.0, 2.0]


def test_absolute_errors_length_mismatch() -> None:
    with pytest.raises(ValueError):
        absolute_errors([1.0], [1.0, 2.0])


def test_mae() -> None:
    assert mae([1.0, 2.0, 3.0], [2.0, 2.0, 1.0]) == 1.0


def test_mae_perfect_forecast() -> None:
    assert mae([5.0, 6.0], [5.0, 6.0]) == 0.0


def test_mae_length_mismatch() -> None:
    with pytest.raises(ValueError):
        mae([1.0], [1.0, 2.0])


def test_mae_empty() -> None:
    with pytest.raises(ValueError):
        mae([], [])


def test_mean_error_keeps_the_sign() -> None:
    assert mean_error([3.0, 3.0], [1.0, 2.0]) == 1.5
    assert mean_error([1.0, 1.0], [2.0, 2.0]) == -1.0


def test_mean_error_cancels_out() -> None:
    assert mean_error([2.0, 0.0], [1.0, 1.0]) == 0.0


def test_rmse() -> None:
    assert rmse([3.0, 5.0], [0.0, 2.0]) == 3.0


def test_rmse_weights_big_errors_more_than_mae() -> None:
    forecast, observed = [0.0, 0.0, 0.0, 8.0], [0.0, 0.0, 0.0, 0.0]
    assert mae(forecast, observed) == 2.0
    assert rmse(forecast, observed) == 4.0


def test_percentile() -> None:
    assert percentile([0.0, 10.0], 50) == 5.0
    assert percentile(list(range(101)), 95) == 95.0


def test_percentile_empty() -> None:
    with pytest.raises(ValueError):
        percentile([], 95)
