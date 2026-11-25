"""The checks that every run applies. To add a check, add its function to CHECKS."""

from collections.abc import Callable

from alerting.checks.big_errors import check_big_errors
from alerting.checks.zigzag import check_zigzag
from alerting.config import Settings
from alerting.models import CheckResult, Data

type Check = Callable[[Data, Settings], list[CheckResult]]

CHECKS: list[Check] = [check_big_errors, check_zigzag]
