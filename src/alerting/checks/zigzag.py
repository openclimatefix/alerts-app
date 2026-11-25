"""Check that the newest forecast does not zigzag."""

from collections.abc import Sequence

from alerting.config import Settings
from alerting.models import CheckResult, Data, Forecast


def count_turns(values: Sequence[float], min_step: float) -> int:
    """Count the changes of direction, ignoring moves of min_step or less."""
    turns = 0
    direction = 0
    last = values[0]
    for value in values[1:]:
        step = value - last
        if abs(step) <= min_step:
            continue
        new_direction = 1 if step > 0 else -1
        if direction and new_direction != direction:
            turns += 1
        direction = new_direction
        last = value
    return turns


def newest_run(forecast: Sequence[Forecast]) -> list[Forecast]:
    """Keep only the values from the forecast that was made last, in time order."""
    newest = max(f.made_at for f in forecast)
    return sorted((f for f in forecast if f.made_at == newest), key=lambda f: f.time)


def check_zigzag(data: Data, settings: Settings) -> list[CheckResult]:
    """Fail when the newest forecast changes direction too many times."""
    if not data.latest_forecast:
        return [CheckResult("zigzag", False, "no forecast found for the next hours")]

    run = newest_run(data.latest_forecast)
    min_step_mw = settings.zigzag_min_step_pct / 100 * run[0].capacity_mw
    turns = count_turns([f.mw for f in run], min_step_mw)
    message = (
        f"changes of direction: {turns} (limit {settings.zigzag_max_turns}), in the next "
        f"{settings.zigzag_hours:g} hours of the forecast made at {run[0].made_at:%Y-%m-%d %H:%M}."
    )
    return [CheckResult("zigzag", turns <= settings.zigzag_max_turns, message)]
