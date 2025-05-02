from unittest.mock import ANY

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i18.d7positionerB import D7PositionerB, FilterBValues


@pytest.fixture
async def positioner() -> D7PositionerB:
    async with init_devices(mock=True):
        positioner = D7PositionerB(prefix="POS:")
    return positioner


async def test_filter_a_setpoint(positioner: D7PositionerB):
    """
    Test setting x and y positions on the KBMirror using the ophyd_async mock tools.
    """
    # Mock the initial values of the x and y signals
    set_mock_value(positioner.setpoint, FilterBValues.DIAMOND_THICK)

    # Call set to update the position
    await positioner.setpoint.set(FilterBValues.AU_DRAIN)

    reading = await positioner.read()
    expected_reading = {
        "positioner-setpoint": {
            "value": FilterBValues.AU_DRAIN,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "positioner-done": {"value": 0.0, "timestamp": ANY, "alarm_severity": 0},
    }

    assert reading == expected_reading
