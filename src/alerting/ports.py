"""Interfaces the app uses to reach the outside world."""

from datetime import datetime
from typing import Protocol

from alerting.models import Forecast, Observation


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
