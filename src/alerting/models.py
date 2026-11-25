"""Plain data types shared by the checks and the adapters."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Forecast:
    """A forecast value for one time."""

    time: datetime
    mw: float
    capacity_mw: float
    made_at: datetime


@dataclass(frozen=True)
class Observation:
    """An observed value at one time."""

    time: datetime
    mw: float
    capacity_mw: float


@dataclass(frozen=True)
class Data:
    """Everything the checks need, pulled once at the start of a run."""

    observed: list[Observation]
    forecasts: dict[int, list[Forecast]]  # horizon in minutes -> forecast for the time window
    latest_forecast: list[Forecast]  # forecast for the next few hours


@dataclass(frozen=True)
class CheckResult:
    """The outcome of one check."""

    name: str
    passed: bool
    message: str
