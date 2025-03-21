from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import set_mock_value

from dodal.devices.hutch_shutter import (
    ShutterState,
)
from dodal.devices.i19.shutter import (
    AccessControlledShutter,
    HutchState,
)


@pytest.fixture
async def eh2_shutter(RE: RunEngine) -> AccessControlledShutter:
    shutter = AccessControlledShutter("", HutchState.EH2, name="mock_shutter")
    await shutter.connect(mock=True)

    shutter.url = "http://test-blueapi.url"
    set_mock_value(shutter.shutter_status, ShutterState.CLOSED)
    return shutter


async def test_read_on_shutter_device_returns_correct_status(
    eh2_shutter: AccessControlledShutter,
):
    reading = await eh2_shutter.read()
    assert reading == {
        "number_of_lenses": {
            "timestamp": ANY,
            "value": "Closed",
        }
    }


def test_set_corrently_makes_rest_calls():
    pass
