"""Send check results to the log."""

import logging
from collections.abc import Sequence

from alerting.models import CheckResult

log = logging.getLogger(__name__)


class LogNotifier:
    """Logs one line per check, then a summary."""

    async def notify(self, results: Sequence[CheckResult]) -> None:
        """Log the results."""
        for result in results:
            log.info("%s %s: %s", "PASS" if result.passed else "FAIL", result.name, result.message)
        failed = sum(not result.passed for result in results)
        if failed:
            log.info("%d of %d checks failed", failed, len(results))
        else:
            log.info("All %d checks passed", len(results))
