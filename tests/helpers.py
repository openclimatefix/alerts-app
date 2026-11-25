from dataclasses import replace
from datetime import UTC, datetime, timedelta

from alerting.config import Settings, load_settings
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


def settings(**changes: object) -> Settings:
    """The default settings, with some values changed."""
    return replace(load_settings({"DATA_PLATFORM_HOST": "localhost"}), **changes)
