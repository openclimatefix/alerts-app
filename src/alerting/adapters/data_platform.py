"""Read forecasts and observations from the data platform."""

from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from grpclib.client import Channel
from ocf import dp

from alerting.config import DataPlatformSettings
from alerting.models import Forecast, Observation

# The data platform allows 31 days per request
MAX_WINDOW = timedelta(days=30)


def chunks(start: datetime, end: datetime) -> Iterator[tuple[datetime, datetime]]:
    """Split a time window into pieces the data platform accepts."""
    while start < end:
        chunk_end = min(start + MAX_WINDOW, end)
        yield start, chunk_end
        start = chunk_end


async def get_national_location_uuid(
    client: dp.DataPlatformDataServiceStub, country_code: str
) -> str:
    """Find the national solar location of a country."""
    response = await client.list_locations(
        dp.ListLocationsRequest(
            location_type_filter=dp.LocationType.NATION,
            energy_source_filter=dp.EnergySource.SOLAR,
            country_code_filter=country_code,
        )
    )
    if len(response.locations) != 1:
        raise ValueError(
            f"Expected one national location for {country_code}, found {len(response.locations)}"
        )
    return response.locations[0].location_uuid


@dataclass(frozen=True)
class DataPlatform:
    """The forecasts and observations of one location in the data platform."""

    client: dp.DataPlatformDataServiceStub
    location_uuid: str
    forecaster: dp.Forecaster
    observer_name: str

    async def get_forecast(
        self, horizon_mins: int, start: datetime, end: datetime
    ) -> list[Forecast]:
        """Forecast in MW for each time in the window, made at least horizon_mins ahead."""
        forecasts: dict[datetime, Forecast] = {}
        for chunk_start, chunk_end in chunks(start, end):
            response = await self.client.get_forecast_as_timeseries(
                dp.GetForecastAsTimeseriesRequest(
                    location_uuid=self.location_uuid,
                    energy_source=dp.EnergySource.SOLAR,
                    horizon_mins=horizon_mins,
                    time_window=dp.TimeWindow(
                        start_timestamp_utc=chunk_start, end_timestamp_utc=chunk_end
                    ),
                    forecaster=self.forecaster,
                )
            )
            for v in response.values:
                capacity_mw = v.effective_capacity_watts / 1e6
                forecasts[v.target_timestamp_utc] = Forecast(
                    time=v.target_timestamp_utc,
                    mw=v.p50_value_fraction * capacity_mw,
                    capacity_mw=capacity_mw,
                    made_at=v.initialization_timestamp_utc,
                )
        return [forecasts[time] for time in sorted(forecasts)]

    async def get_observations(self, start: datetime, end: datetime) -> list[Observation]:
        """Observed generation in MW for each time in the window."""
        observations: dict[datetime, Observation] = {}
        for chunk_start, chunk_end in chunks(start, end):
            response = await self.client.get_observations_as_timeseries(
                dp.GetObservationsAsTimeseriesRequest(
                    location_uuid=self.location_uuid,
                    observer_name=self.observer_name,
                    energy_source=dp.EnergySource.SOLAR,
                    time_window=dp.TimeWindow(
                        start_timestamp_utc=chunk_start, end_timestamp_utc=chunk_end
                    ),
                )
            )
            for v in response.values:
                capacity_mw = v.effective_capacity_watts / 1e6
                observations[v.timestamp_utc] = Observation(
                    time=v.timestamp_utc,
                    mw=v.value_fraction * capacity_mw,
                    capacity_mw=capacity_mw,
                )
        return [observations[time] for time in sorted(observations)]


@asynccontextmanager
async def open_data_platform(settings: DataPlatformSettings) -> AsyncGenerator[DataPlatform]:
    """Connect to the data platform and find the country's national location."""
    async with Channel(host=settings.host, port=settings.port) as channel:
        # Every request fails after the timeout, so a stalled data platform cannot block the run
        client = dp.DataPlatformDataServiceStub(channel, timeout=settings.timeout_secs)
        yield DataPlatform(
            client=client,
            location_uuid=await get_national_location_uuid(client, settings.country_code),
            forecaster=dp.Forecaster(
                forecaster_name=settings.forecaster_name,
                forecaster_version=settings.forecaster_version,
            ),
            observer_name=settings.observer_name,
        )
