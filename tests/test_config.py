import pytest

from alerting.config import load_check_settings, load_data_platform_settings, load_limits_settings


def test_defaults() -> None:
    data_platform = load_data_platform_settings({"DATA_PLATFORM_HOST": "localhost"})
    assert data_platform.port == 50051
    assert data_platform.timeout_secs == 60.0
    assert data_platform.country_code == "GB"
    assert data_platform.forecaster_version == ""

    checks = load_check_settings({})
    assert checks.horizons_mins == [60, 120]
    assert checks.error_limit_pct == 10.0

    assert load_limits_settings({}).history_days == 90


def test_values_from_the_environment() -> None:
    settings = load_check_settings({"HORIZON_MINS": "0, 30", "ERROR_LIMIT_PCT": "7.5"})
    assert settings.horizons_mins == [0, 30]
    assert settings.error_limit_pct == 7.5


@pytest.mark.parametrize("env", [{}, {"DATA_PLATFORM_HOST": " "}])
def test_host_is_required(env: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="DATA_PLATFORM_HOST"):
        load_data_platform_settings(env)


def test_names_must_not_be_empty() -> None:
    with pytest.raises(ValueError, match="FORECASTER_NAME"):
        load_data_platform_settings({"DATA_PLATFORM_HOST": "localhost", "FORECASTER_NAME": ""})


def test_bad_number_is_an_error() -> None:
    with pytest.raises(ValueError):
        load_check_settings({"ERROR_LIMIT_PCT": "ten"})


@pytest.mark.parametrize("horizons", ["", "60,", "-60"])
def test_bad_horizons_are_an_error(horizons: str) -> None:
    with pytest.raises(ValueError):
        load_check_settings({"HORIZON_MINS": horizons})


@pytest.mark.parametrize("name", ["WINDOW_HOURS", "ZIGZAG_HOURS"])
def test_hours_must_be_above_zero(name: str) -> None:
    with pytest.raises(ValueError, match=name):
        load_check_settings({name: "0"})


def test_history_days_must_be_above_zero() -> None:
    with pytest.raises(ValueError, match="HISTORY_DAYS"):
        load_limits_settings({"HISTORY_DAYS": "-1"})
