import asyncio
import logging

import pytest

from alerting.adapters.log_notifier import LogNotifier
from alerting.models import CheckResult


def test_logs_each_result_and_a_summary(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    results = [CheckResult("a", True, "fine"), CheckResult("b", False, "broken")]
    asyncio.run(LogNotifier().notify(results))
    assert caplog.messages == ["PASS a: fine", "FAIL b: broken", "1 of 2 checks failed"]


def test_all_passed(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    asyncio.run(LogNotifier().notify([CheckResult("a", True, "fine")]))
    assert caplog.messages[-1] == "All 1 checks passed"
