import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta

import pytest
from grpclib.testing import ChannelFor
from ocf import dp

from alerting.adapters.data_platform import DataPlatform, chunks, get_national_location_uuid
from tests.helpers import START

CAPACITY_WATTS = 2_000_000_000


class FakeDataPlatform(dp.DataPlatformDataServiceBase):
    """A data platform that answers from memory and keeps each request."""

    def __init__(self, locations: list[str] | None = None) -> None:
        self.locations = locations or []
        self.requests: list[object] = []

    async def get_forecast_as_timeseries(
        self, get_forecast_as_timeseries_request: dp.GetForecastAsTimeseriesRequest
    ) -> dp.GetForecastAsTimeseriesResponse:
        # One value at each end of the window
        self.requests.append(get_forecast_as_timeseries_request)
        window = get_forecast_as_timeseries_request.time_window
        return dp.GetForecastAsTimeseriesResponse(
            values=[
                dp.GetForecastAsTimeseriesResponseValue(
                    target_timestamp_utc=time,
                    p50_value_fraction=0.5,
                    effective_capacity_watts=CAPACITY_WATTS,
                    initialization_timestamp_utc=time - timedelta(hours=1),
                )
                for time in (window.start_timestamp_utc, window.end_timestamp_utc)
            ]
        )

    async def get_observations_as_timeseries(
        self, get_observations_as_timeseries_request: dp.GetObservationsAsTimeseriesRequest
    ) -> dp.GetObservationsAsTimeseriesResponse:
        self.requests.append(get_observations_as_timeseries_request)
        window = get_observations_as_timeseries_request.time_window
        return dp.GetObservationsAsTimeseriesResponse(
            values=[
                dp.GetObservationsAsTimeseriesResponseValue(
                    timestamp_utc=window.start_timestamp_utc,
                    value_fraction=0.25,
                    effective_capacity_watts=CAPACITY_WATTS,
                )
            ]
        )

    async def list_locations(
        self, list_locations_request: dp.ListLocationsRequest
    ) -> dp.ListLocationsResponse:
        self.requests.append(list_locations_request)
        return dp.ListLocationsResponse(
            locations=[
                dp.ListLocationsResponseLocationSummary(location_uuid=uuid)
                for uuid in self.locations
            ]
        )


def call[T](
    server: FakeDataPlatform, use: Callable[[dp.DataPlatformDataServiceStub], Awaitable[T]]
) -> T:
    """Use a client that talks to the fake data platform over an in-memory connection."""

    async def connect() -> T:
        async with ChannelFor([server]) as channel:
            return await use(dp.DataPlatformDataServiceStub(channel))

    return asyncio.run(connect())


def platform(client: dp.DataPlatformDataServiceStub) -> DataPlatform:
    return DataPlatform(
        client=client,
        location_uuid="0199a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5b",
        forecaster=dp.Forecaster(forecaster_name="blend"),
        observer_name="pvlive_in_day",
    )


def test_chunks_split_a_long_window() -> None:
    end = START + timedelta(days=70)
    assert list(chunks(START, end)) == [
        (START, START + timedelta(days=30)),
        (START + timedelta(days=30), START + timedelta(days=60)),
        (START + timedelta(days=60), end),
    ]


def test_chunks_keep_a_short_window_whole() -> None:
    end = START + timedelta(hours=24)
    assert list(chunks(START, end)) == [(START, end)]


def test_forecast_is_in_mw() -> None:
    server = FakeDataPlatform()
    end = START + timedelta(hours=24)
    first, last = call(server, lambda client: platform(client).get_forecast(60, START, end))

    assert (first.time, last.time) == (START, end)
    assert first.mw == 1000.0
    assert first.capacity_mw == 2000.0
    assert first.made_at == START - timedelta(hours=1)

    [request] = server.requests
    assert isinstance(request, dp.GetForecastAsTimeseriesRequest)
    assert request.horizon_mins == 60
    assert request.energy_source == dp.EnergySource.SOLAR
    assert request.forecaster.forecaster_name == "blend"
    assert request.forecaster.forecaster_version == ""


def test_long_forecast_window_uses_several_requests() -> None:
    server = FakeDataPlatform()
    end = START + timedelta(days=70)
    forecasts = call(server, lambda client: platform(client).get_forecast(0, START, end))

    assert len(server.requests) == 3
    # Values on a chunk boundary come back twice but are kept once
    assert [f.time for f in forecasts] == [
        START,
        START + timedelta(days=30),
        START + timedelta(days=60),
        end,
    ]


def test_observations_are_in_mw() -> None:
    server = FakeDataPlatform()
    end = START + timedelta(hours=24)
    [observation] = call(server, lambda client: platform(client).get_observations(START, end))

    assert observation.time == START
    assert observation.mw == 500.0
    assert observation.capacity_mw == 2000.0

    [request] = server.requests
    assert isinstance(request, dp.GetObservationsAsTimeseriesRequest)
    assert request.observer_name == "pvlive_in_day"


def test_national_location() -> None:
    server = FakeDataPlatform(locations=["gb-uuid"])
    assert call(server, lambda client: get_national_location_uuid(client, "GB")) == "gb-uuid"

    [request] = server.requests
    assert isinstance(request, dp.ListLocationsRequest)
    assert request.country_code_filter == "GB"
    assert request.location_type_filter == dp.LocationType.NATION
    assert request.energy_source_filter == dp.EnergySource.SOLAR


def test_national_location_must_be_unique() -> None:
    server = FakeDataPlatform(locations=[])
    with pytest.raises(ValueError, match="found 0"):
        call(server, lambda client: get_national_location_uuid(client, "GB"))
