from unittest.mock import ANY

import pytest
from ophyd_async.core import DeviceCollector, set_mock_value

from dodal.devices.i18.KBMirror import KBMirror, XYPosition


@pytest.fixture
async def kbmirror() -> KBMirror:
    """Fixture to set up a mock KBMirror device using DeviceCollector."""
    async with DeviceCollector(mock=True):
        kbmirror = KBMirror(prefix="MIRROR:")
    return kbmirror


async def test_setting_xy_position_kbmirror(kbmirror: KBMirror):
    """
    Test setting x and y positions on the KBMirror using the ophyd_async mock tools.
    """
    # Mock the initial values of the x and y signals
    set_mock_value(kbmirror.x, 0.0)
    set_mock_value(kbmirror.y, 0.0)

    # Create a position object
    position = XYPosition(x=1.23, y=4.56)

    # Call set_xy to update the position
    await kbmirror.set(position)

    reading = await kbmirror.read()
    expected_reading = {
        "kbmirror-y": {
            "value": 4.56,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "kbmirror-bend1": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "kbmirror-ellip": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "kbmirror-x": {
            "value": 1.23,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "kbmirror-bend2": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "kbmirror-curve": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
    }

    assert reading == expected_reading