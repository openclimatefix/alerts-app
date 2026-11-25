"""Entrypoint: run the checks on recent forecasts and observations."""

import asyncio
import logging
import sys
from datetime import UTC, datetime, timedelta

from alerting.adapters.data_platform import open_data_platform
from alerting.checks import CHECKS
from alerting.config import Settings, load_settings
from alerting.models import CheckResult, Data
from alerting.ports import DataSource

log = logging.getLogger(__name__)


async def load_data(source: DataSource, settings: Settings, now: datetime) -> Data:
    """Pull everything the checks need into memory."""
    start = now - timedelta(hours=settings.window_hours)
    zigzag_end = now + timedelta(hours=settings.zigzag_hours)
    return Data(
        observed=await source.get_observations(start, now),
        forecasts={h: await source.get_forecast(h, start, now) for h in settings.horizons_mins},
        latest_forecast=await source.get_forecast(0, now, zigzag_end),
    )


def run_checks(data: Data, settings: Settings) -> list[CheckResult]:
    """Apply every check to the data."""
    return [result for check in CHECKS for result in check(data, settings)]


def report(results: list[CheckResult]) -> int:
    """Log one line per check and return the exit code."""
    for result in results:
        log.info("%s %s: %s", "PASS" if result.passed else "FAIL", result.name, result.message)
    failed = sum(not result.passed for result in results)
    if failed:
        log.info("%d of %d checks failed", failed, len(results))
        return 1
    log.info("All %d checks passed", len(results))
    return 0


async def run() -> list[CheckResult]:
    """Do one full run against the data platform."""
    settings = load_settings()
    async with open_data_platform(settings) as source:
        data = await load_data(source, settings, datetime.now(UTC))
    return run_checks(data, settings)


def main() -> None:
    """Run the checks and exit with 1 if any failed."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    sys.exit(report(asyncio.run(run())))
