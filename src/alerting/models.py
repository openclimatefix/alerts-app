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
class CheckResult:
    """The outcome of one check."""

    name: str
    passed: bool
    message: str
