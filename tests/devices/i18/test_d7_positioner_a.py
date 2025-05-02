from unittest.mock import ANY

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i18.d7positionerA import D7PositionerA, FilterAValues


@pytest.fixture
async def positioner() -> D7PositionerA:
    async with init_devices(mock=True):
        positioner = D7PositionerA(prefix="POS:")
    return positioner


async def test_filter_a_setpoint(positioner: D7PositionerA):
    """
    Test setting x and y positions on the KBMirror using the ophyd_async mock tools.
    """
    # Mock the initial values of the x and y signals
    set_mock_value(positioner.setpoint, FilterAValues.AL_0_025MM)

    # Call set to update the position
    await positioner.setpoint.set(FilterAValues.AL_2MM)

    reading = await positioner.read()
    expected_reading = {
        "positioner-setpoint": {
            "value": FilterAValues.AL_2MM,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "positioner-done": {"value": 0.0, "timestamp": ANY, "alarm_severity": 0},
    }

    assert reading == expected_reading
