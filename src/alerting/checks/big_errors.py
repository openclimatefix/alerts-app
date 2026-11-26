"""Check for big forecast errors."""

from collections.abc import Sequence
from datetime import datetime, timedelta

from alerting.checks.errors import mae, mean_error, rmse
from alerting.config import CheckSettings
from alerting.models import CheckResult, Forecast, Observation
from alerting.ports import DataSource

type Pair = tuple[Forecast, Observation]


def pair(forecast: Sequence[Forecast], observed: Sequence[Observation]) -> list[Pair]:
    """Match each forecast value with the observation at the same time."""
    observed_at = {o.time: o for o in observed}
    return [(f, observed_at[f.time]) for f in forecast if f.time in observed_at]


def error_pct(forecast: Forecast, observed: Observation) -> float:
    """Absolute error as % of capacity."""
    return abs(forecast.mw - observed.mw) * 100 / observed.capacity_mw


def biggest_error(pairs: Sequence[Pair]) -> Pair:
    """The pair with the biggest error."""
    return max(pairs, key=lambda p: error_pct(*p))


async def check_big_errors(
    source: DataSource, settings: CheckSettings, now: datetime
) -> list[CheckResult]:
    """Fail when the biggest error at a horizon in the last few hours is above the limit."""
    start = now - timedelta(hours=settings.window_hours)
    observed = await source.get_observations(start, now)
    return [
        _check_horizon(
            horizon,
            pair(await source.get_forecast(horizon, start, now), observed),
            settings.error_limit_pct,
        )
        for horizon in settings.horizons_mins
    ]


def _check_horizon(horizon: int, pairs: list[Pair], limit_pct: float) -> CheckResult:
    name = f"big_error_{horizon}min"
    if not pairs:
        return CheckResult(name, False, "no forecast and observation at the same times")

    forecast, observed = biggest_error(pairs)
    pct = error_pct(forecast, observed)
    forecast_mw = [f.mw for f, _ in pairs]
    observed_mw = [o.mw for _, o in pairs]
    message = (
        f"biggest error {abs(forecast.mw - observed.mw):.0f} MW ({pct:.1f}% of capacity, "
        f"limit {limit_pct:g}%) at {forecast.time:%Y-%m-%d %H:%M}. "
        f"Forecast {forecast.mw:.0f} MW made at {forecast.made_at:%Y-%m-%d %H:%M}, "
        f"observed {observed.mw:.0f} MW. "
        f"MAE {mae(forecast_mw, observed_mw):.0f} MW, "
        f"mean error {mean_error(forecast_mw, observed_mw):+.0f} MW, "
        f"RMSE {rmse(forecast_mw, observed_mw):.0f} MW over {len(pairs)} points."
    )
    return CheckResult(name, pct <= limit_pct, message)
