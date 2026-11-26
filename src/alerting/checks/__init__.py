"""The checks that every run applies. To add a check, add its function to CHECKS."""

from collections.abc import Awaitable, Callable
from datetime import datetime

from alerting.checks.big_errors import check_big_errors
from alerting.checks.zigzag import check_zigzag
from alerting.config import CheckSettings
from alerting.models import CheckResult
from alerting.ports import DataSource

# A check pulls the data it needs from the source, for times around now
type Check = Callable[[DataSource, CheckSettings, datetime], Awaitable[list[CheckResult]]]

CHECKS: list[Check] = [check_big_errors, check_zigzag]
