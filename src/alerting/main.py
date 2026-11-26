"""Entrypoint: run the checks on recent forecasts and observations."""

import asyncio
import logging
import sys
from datetime import UTC, datetime

from alerting.adapters.data_platform import open_data_platform
from alerting.adapters.log_notifier import LogNotifier
from alerting.checks import CHECKS
from alerting.config import CheckSettings, load_check_settings, load_data_platform_settings
from alerting.models import CheckResult
from alerting.ports import DataSource, Notifier


async def run(
    source: DataSource, notifier: Notifier, settings: CheckSettings, now: datetime
) -> list[CheckResult]:
    """Apply every check and send the results to the notifier."""
    results = [result for check in CHECKS for result in await check(source, settings, now)]
    await notifier.notify(results)
    return results


async def run_against_data_platform() -> int:
    """Wire up the real adapters, do one run, and return the exit code."""
    data_platform_settings = load_data_platform_settings()
    check_settings = load_check_settings()
    async with open_data_platform(data_platform_settings) as source:
        results = await run(source, LogNotifier(), check_settings, datetime.now(UTC))
    return 0 if all(result.passed for result in results) else 1


def main() -> None:
    """Run the checks and exit with 1 if any failed."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    sys.exit(asyncio.run(run_against_data_platform()))
