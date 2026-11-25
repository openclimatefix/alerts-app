"""Settings read from environment variables."""

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """The settings for one run."""

    data_platform_host: str
    data_platform_port: int
    country_code: str
    forecaster_name: str
    forecaster_version: str
    observer_name: str
    horizons_mins: list[int]
    window_hours: float
    error_limit_pct: float
    zigzag_hours: float
    zigzag_min_step_pct: float
    zigzag_max_turns: int
    history_days: int


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    """Read the settings, with a default for everything except the host."""
    return Settings(
        data_platform_host=env["DATA_PLATFORM_HOST"],
        data_platform_port=int(env.get("DATA_PLATFORM_PORT", "50051")),
        country_code=env.get("COUNTRY_CODE", "GB"),
        forecaster_name=env.get("FORECASTER_NAME", "blend"),
        forecaster_version=env.get("FORECASTER_VERSION", ""),
        observer_name=env.get("OBSERVER_NAME", "pvlive_in_day"),
        horizons_mins=[int(h) for h in env.get("HORIZON_MINS", "60,120").split(",")],
        window_hours=float(env.get("WINDOW_HOURS", "24")),
        error_limit_pct=float(env.get("ERROR_LIMIT_PCT", "10")),
        zigzag_hours=float(env.get("ZIGZAG_HOURS", "8")),
        zigzag_min_step_pct=float(env.get("ZIGZAG_MIN_STEP_PCT", "2")),
        zigzag_max_turns=int(env.get("ZIGZAG_MAX_TURNS", "1")),
        history_days=int(env.get("HISTORY_DAYS", "90")),
    )
