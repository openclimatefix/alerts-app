import pytest

from alerting.config import load_settings


def test_defaults() -> None:
    settings = load_settings({"DATA_PLATFORM_HOST": "localhost"})
    assert settings.data_platform_port == 50051
    assert settings.country_code == "GB"
    assert settings.forecaster_version == ""
    assert settings.horizons_mins == [60, 120]
    assert settings.error_limit_pct == 10.0


def test_values_from_the_environment() -> None:
    settings = load_settings(
        {"DATA_PLATFORM_HOST": "localhost", "HORIZON_MINS": "0, 30", "ERROR_LIMIT_PCT": "7.5"}
    )
    assert settings.horizons_mins == [0, 30]
    assert settings.error_limit_pct == 7.5


def test_host_is_required() -> None:
    with pytest.raises(KeyError, match="DATA_PLATFORM_HOST"):
        load_settings({})


def test_bad_number_is_an_error() -> None:
    with pytest.raises(ValueError):
        load_settings({"DATA_PLATFORM_HOST": "localhost", "ERROR_LIMIT_PCT": "ten"})
