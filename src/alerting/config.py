"""Settings read from environment variables."""

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class DataPlatformSettings:
    """Where to read forecasts and observations from."""

    host: str
    port: int
    timeout_secs: float
    country_code: str
    forecaster_name: str
    forecaster_version: str
    observer_name: str


@dataclass(frozen=True)
class CheckSettings:
    """The settings of the checks."""

    horizons_mins: list[int]
    window_hours: float
    error_limit_pct: float
    zigzag_hours: float
    zigzag_min_step_pct: float
    zigzag_max_turns: int


@dataclass(frozen=True)
class LimitsSettings:
    """The settings of calc-limits."""

    horizons_mins: list[int]
    history_days: int


def _text(env: Mapping[str, str], name: str, default: str = "") -> str:
    value = env.get(name, default).strip()
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value


def _above_zero[N: (int, float)](name: str, value: N) -> N:
    if value <= 0:
        raise ValueError(f"{name} must be above 0, got {value}")
    return value


def _horizons(env: Mapping[str, str]) -> list[int]:
    horizons = [int(h) for h in env.get("HORIZON_MINS", "60,120").split(",")]
    if any(h < 0 for h in horizons):
        raise ValueError(f"HORIZON_MINS must not be negative, got {horizons}")
    return horizons


def load_data_platform_settings(env: Mapping[str, str] = os.environ) -> DataPlatformSettings:
    """Read the data platform settings, with a default for everything except the host."""
    return DataPlatformSettings(
        host=_text(env, "DATA_PLATFORM_HOST"),
        port=int(env.get("DATA_PLATFORM_PORT", "50051")),
        timeout_secs=_above_zero(
            "DATA_PLATFORM_TIMEOUT_SECS", float(env.get("DATA_PLATFORM_TIMEOUT_SECS", "60"))
        ),
        country_code=_text(env, "COUNTRY_CODE", "GB"),
        forecaster_name=_text(env, "FORECASTER_NAME", "blend"),
        forecaster_version=env.get("FORECASTER_VERSION", ""),
        observer_name=_text(env, "OBSERVER_NAME", "pvlive_in_day"),
    )


def load_check_settings(env: Mapping[str, str] = os.environ) -> CheckSettings:
    """Read the check settings, with a default for everything."""
    return CheckSettings(
        horizons_mins=_horizons(env),
        window_hours=_above_zero("WINDOW_HOURS", float(env.get("WINDOW_HOURS", "24"))),
        error_limit_pct=float(env.get("ERROR_LIMIT_PCT", "10")),
        zigzag_hours=_above_zero("ZIGZAG_HOURS", float(env.get("ZIGZAG_HOURS", "8"))),
        zigzag_min_step_pct=float(env.get("ZIGZAG_MIN_STEP_PCT", "2")),
        zigzag_max_turns=int(env.get("ZIGZAG_MAX_TURNS", "1")),
    )


def load_limits_settings(env: Mapping[str, str] = os.environ) -> LimitsSettings:
    """Read the calc-limits settings, with a default for everything."""
    return LimitsSettings(
        horizons_mins=_horizons(env),
        history_days=_above_zero("HISTORY_DAYS", int(env.get("HISTORY_DAYS", "90"))),
    )
