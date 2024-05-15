from unittest import mock

import pytest
from ophyd_async.core import DeviceCollector, set_mock_value

from dodal.devices.i22.fswitch import FilterState, FSwitch


@pytest.fixture
async def fswitch() -> FSwitch:
    async with DeviceCollector(mock=True):
        fswitch = FSwitch("DEMO-FSWT-01:")

    return fswitch


async def test_reading_fswitch(fswitch: FSwitch):
    set_mock_value(fswitch.filters.get(0), FilterState.OUT_BEAM)
    set_mock_value(fswitch.filters.get(1), FilterState.OUT_BEAM)
    set_mock_value(fswitch.filters.get(2), FilterState.OUT_BEAM)

    reading = await fswitch.read()
    assert reading == {
        "number_of_lenses": {
            "timestamp": mock.ANY,
            "value": 125,  # three filters out
        }
    }
