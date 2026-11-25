# alerting

Checks our solar forecasts against observations and fails when something looks wrong.
It is made to run in Airflow, where a failed run sends a Slack message.

## What it checks

| Check | Fails when |
| --- | --- |
| `big_error_<horizon>min` | The biggest error in the time window is above `ERROR_LIMIT_PCT`. There is one check per horizon. |
| `zigzag` | The newest forecast changes direction more than `ZIGZAG_MAX_TURNS` times in the next `ZIGZAG_HOURS` hours. |

A check also fails when its data is missing.

We look at the biggest error, not an average. One bad half hour barely moves the MAE, but it is
what a client notices. MAE, mean error and RMSE are still logged for context.

## Run it

```bash
uv sync
export DATA_PLATFORM_HOST=<host>
uv run check-alerts
```

It logs one line per check:

```
PASS big_error_60min: biggest error 387 MW (1.8% of capacity, limit 10%) at 2026-06-14 12:00. Forecast 13287 MW made at 2026-06-14 11:00, observed 12900 MW. MAE 117 MW, mean error +117 MW, RMSE 190 MW over 46 points.
FAIL zigzag: changes of direction: 14 (limit 1), in the next 8 hours of the forecast made at 2026-06-15 09:10.
1 of 3 checks failed
```

The exit code is 0 when every check passes and 1 when any check fails.

## Settings

All settings are environment variables.

| Variable | Default | Meaning |
| --- | --- | --- |
| `DATA_PLATFORM_HOST` | required | Data platform host |
| `DATA_PLATFORM_PORT` | `50051` | Data platform port |
| `COUNTRY_CODE` | `GB` | Country whose national solar forecast is checked |
| `FORECASTER_NAME` | `blend` | Forecaster to check |
| `FORECASTER_VERSION` | empty | Forecaster version. Empty means the latest |
| `OBSERVER_NAME` | `pvlive_in_day` | Observations to compare against |
| `HORIZON_MINS` | `60,120` | Horizons to check, in minutes |
| `WINDOW_HOURS` | `24` | How far back to look for errors |
| `ERROR_LIMIT_PCT` | `10` | Biggest error allowed, as % of capacity |
| `ZIGZAG_HOURS` | `8` | How much of the newest forecast the zigzag check looks at |
| `ZIGZAG_MIN_STEP_PCT` | `2` | Moves of this size or less are ignored, as % of capacity |
| `ZIGZAG_MAX_TURNS` | `1` | Changes of direction allowed |
| `HISTORY_DAYS` | `90` | Days of history that `calc-limits` uses |

## Choose the error limit

```bash
uv run calc-limits
```

This pulls the last `HISTORY_DAYS` days and finds the biggest error of each day. It logs the 95th
and 99th percentile of those daily values, the five worst days, and a line per month. Use it to
choose `ERROR_LIMIT_PCT`. It reads the same settings as `check-alerts`.

If the data platform has no data that far back, the request can fail. Lower `HISTORY_DAYS`.

## Develop

```bash
uv run pytest
uv run ruff check
uv run ruff format
uv run ty check
```

The tests need no network.

## Layout

```
src/alerting/
  main.py        check-alerts entrypoint
  limits.py      calc-limits entrypoint
  config.py      settings from environment variables
  models.py      plain data types
  ports.py       interface for reading data
  checks/        the checks, as pure functions
  adapters/      data platform client
```

To add a check, write a function that takes the data and the settings and returns a list of
results. Then add it to `CHECKS` in `src/alerting/checks/__init__.py`.
