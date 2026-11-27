from dataclasses import replace
from datetime import UTC, datetime, timedelta

from alerting.config import CheckSettings, load_check_settings
from alerting.models import Forecast, Observation

START = datetime(2026, 6, 1, tzinfo=UTC)
CAPACITY_MW = 1000.0


def forecasts(
    values: list[float], start: datetime = START, made_at: datetime = START
) -> list[Forecast]:
    """Half-hourly forecast values."""
    return [
        Forecast(start + timedelta(minutes=30 * i), mw, CAPACITY_MW, made_at)
        for i, mw in enumerate(values)
    ]


def observations(values: list[float], start: datetime = START) -> list[Observation]:
    """Half-hourly observed values."""
    return [
        Observation(start + timedelta(minutes=30 * i), mw, CAPACITY_MW)
        for i, mw in enumerate(values)
    ]


def settings(**changes: object) -> CheckSettings:
    """The default check settings, with some values changed."""
    return replace(load_check_settings({}), **changes)


class FakeSource:
    """A data source that serves values from memory and keeps each request."""

    def __init__(
        self,
        forecast: dict[int, list[Forecast]] | None = None,
        observed: list[Observation] | None = None,
    ) -> None:
        self.forecast = forecast or {}
        self.observed = observed or []
        self.requests: list[tuple[int, datetime, datetime]] = []

    async def get_forecast(
        self, horizon_mins: int, start: datetime, end: datetime
    ) -> list[Forecast]:
        self.requests.append((horizon_mins, start, end))
        return [f for f in self.forecast.get(horizon_mins, []) if start <= f.time <= end]

    async def get_observations(self, start: datetime, end: datetime) -> list[Observation]:
        return [o for o in self.observed if start <= o.time <= end]
