"""Entrypoint: work out an error limit from past forecasts and observations."""

import asyncio
import logging
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta

from alerting.adapters.data_platform import open_data_platform
from alerting.checks.big_errors import Pair, biggest_error, error_pct, pair
from alerting.checks.errors import percentile
from alerting.config import load_data_platform_settings, load_limits_settings
from alerting.models import Forecast, Observation

log = logging.getLogger(__name__)


def daily_biggest_errors(
    forecast: Sequence[Forecast], observed: Sequence[Observation]
) -> list[Pair]:
    """The biggest error of each UTC day, in date order."""
    days: dict[date, list[Pair]] = {}
    for f, o in pair(forecast, observed):
        days.setdefault(f.time.date(), []).append((f, o))
    return [biggest_error(days[day]) for day in sorted(days)]


def report(horizon: int, worst: Sequence[Pair]) -> None:
    """Log the percentiles of the daily biggest errors, the worst days, and each month."""
    if not worst:
        log.info("Horizon %d min: no forecast and observation at the same times", horizon)
        return

    first, last = worst[0][0].time.date(), worst[-1][0].time.date()
    log.info("Horizon %d min: %d days from %s to %s", horizon, len(worst), first, last)
    pcts = [error_pct(f, o) for f, o in worst]
    log.info("  P95 of the daily biggest error: %.1f%% of capacity", percentile(pcts, 95))
    log.info("  P99 of the daily biggest error: %.1f%% of capacity", percentile(pcts, 99))

    log.info("  Worst days:")
    for f, o in sorted(worst, key=lambda p: error_pct(*p), reverse=True)[:5]:
        log.info(
            "    %s: %.0f MW (%.1f%%), forecast made at %s",
            f"{f.time:%Y-%m-%d %H:%M}",
            abs(f.mw - o.mw),
            error_pct(f, o),
            f"{f.made_at:%Y-%m-%d %H:%M}",
        )

    log.info("  By month:")
    months: dict[str, list[float]] = {}
    for f, o in worst:
        months.setdefault(f"{f.time:%Y-%m}", []).append(error_pct(f, o))
    for month, month_pcts in months.items():
        log.info(
            "    %s: %d days, P95 %.1f%%, worst %.1f%%",
            month,
            len(month_pcts),
            percentile(month_pcts, 95),
            max(month_pcts),
        )


async def run() -> None:
    """Pull the history and report on each horizon."""
    data_platform_settings = load_data_platform_settings()
    limits_settings = load_limits_settings()
    # Whole UTC days only, so today's part day is left out
    end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=limits_settings.history_days)
    async with open_data_platform(data_platform_settings) as source:
        observed = await source.get_observations(start, end)
        forecasts = {
            h: await source.get_forecast(h, start, end) for h in limits_settings.horizons_mins
        }

    log.info(
        "%s %s against %s, last %d days",
        data_platform_settings.country_code,
        data_platform_settings.forecaster_name,
        data_platform_settings.observer_name,
        limits_settings.history_days,
    )
    for horizon, forecast in forecasts.items():
        report(horizon, daily_biggest_errors(forecast, observed))


def main() -> None:
    """Log the limits that the history suggests."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    asyncio.run(run())
