from unittest import mock

import pytest
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from event_model import DataKey
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i22.fswitch import FilterState, FSwitch


@pytest.fixture
async def fswitch() -> FSwitch:
    async with init_devices(mock=True):
        fswitch = FSwitch(
            "DEMO-FSWT-01:",
            lens_geometry="paraboloid",
            cylindrical=True,
            lens_material="Beryllium",
        )

    return fswitch


async def test_reading_fswitch(fswitch: FSwitch):
    set_mock_value(fswitch.filters[0], FilterState.OUT_BEAM)
    set_mock_value(fswitch.filters[1], FilterState.OUT_BEAM)
    set_mock_value(fswitch.filters[2], FilterState.OUT_BEAM)

    reading = await fswitch.read()
    assert reading == {
        "number_of_lenses": {
            "timestamp": mock.ANY,
            "value": 125,  # three filters out
        }
    }


def test_fswitch_count_plan(RE: RunEngine, fswitch: FSwitch):
    names = []
    docs = []

    def subscription(name, doc):
        names.append(name)
        docs.append(doc)

    RE(count([fswitch]), subscription)

    descriptor_doc = docs[names.index("descriptor")]
    event_doc = docs[names.index("event")]

    expected_data_key = DataKey(
        dtype="integer", shape=[], source="fswitch", object_name="fswitch"
    )
    assert descriptor_doc["data_keys"] == {"number_of_lenses": expected_data_key}

    assert descriptor_doc["configuration"]["fswitch"]["data"] == {
        "fswitch-cylindrical": True,
        "fswitch-lens_geometry": "paraboloid",
        "fswitch-lens_material": "Beryllium",
    }

    expected_data = {"number_of_lenses": 128}
    assert event_doc["data"] == expected_data
