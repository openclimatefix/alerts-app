"""Interfaces the app uses to reach the outside world."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from alerting.models import CheckResult, Forecast, Observation


class DataSource(Protocol):
    """Where forecasts and observations come from."""

    async def get_forecast(
        self, horizon_mins: int, start: datetime, end: datetime
    ) -> list[Forecast]:
        """Forecast for each time in the window, made at least horizon_mins ahead."""
        ...

    async def get_observations(self, start: datetime, end: datetime) -> list[Observation]:
        """Observed value for each time in the window."""
        ...


class Notifier(Protocol):
    """Where check results are sent."""

    async def notify(self, results: Sequence[CheckResult]) -> None:
        """Deliver the results of a run."""
        ...
