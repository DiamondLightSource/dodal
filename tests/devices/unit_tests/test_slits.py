from typing import Any, Mapping
from unittest.mock import ANY

import pytest
from ophyd_async.core import DeviceCollector, StandardReadable, set_mock_value

from dodal.devices.slits import Slits


@pytest.fixture
async def slits() -> Slits:
    async with DeviceCollector(mock=True):
        slits = Slits("DEMO-SLITS-01:")

    return slits


async def test_reading_slits_reads_gaps_and_centres(slits: Slits):
    set_mock_value(slits.x_gap.user_readback, 0.5)
    set_mock_value(slits.y_centre.user_readback, 1.0)
    set_mock_value(slits.y_gap.user_readback, 1.5)

    await assert_reading(
        slits,
        {
            "slits-x_centre": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "slits-x_gap": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.5,
            },
            "slits-y_centre": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 1.0,
            },
            "slits-y_gap": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 1.5,
            },
        },
    )


async def assert_reading(
    device: StandardReadable,
    expected_reading: Mapping[str, Any],
) -> None:
    reading = await device.read()

    assert reading == expected_reading
