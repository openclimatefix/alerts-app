"""Error maths on forecast and observed values, given in the same order."""

from collections.abc import Sequence
from math import sqrt
from statistics import fmean, quantiles


def errors(forecast: Sequence[float], observed: Sequence[float]) -> list[float]:
    """Forecast minus observed at each time."""
    return [f - o for f, o in zip(forecast, observed, strict=True)]


def absolute_errors(forecast: Sequence[float], observed: Sequence[float]) -> list[float]:
    """Absolute error at each time."""
    return [abs(e) for e in errors(forecast, observed)]


def max_absolute_error(forecast: Sequence[float], observed: Sequence[float]) -> float:
    """Largest absolute error across all times."""
    return max(absolute_errors(forecast, observed))


def mae(forecast: Sequence[float], observed: Sequence[float]) -> float:
    """Mean Absolute Error between forecast and observed values."""
    return fmean(absolute_errors(forecast, observed))


def mean_error(forecast: Sequence[float], observed: Sequence[float]) -> float:
    """Mean Error. Positive means the forecast was too high."""
    return fmean(errors(forecast, observed))


def rmse(forecast: Sequence[float], observed: Sequence[float]) -> float:
    """Root Mean Squared Error between forecast and observed values."""
    return sqrt(fmean(e * e for e in errors(forecast, observed)))


def percentile(values: Sequence[float], q: int) -> float:
    """The q-th percentile (1 to 99) of the values."""
    return quantiles(values, n=100, method="inclusive")[q - 1]
