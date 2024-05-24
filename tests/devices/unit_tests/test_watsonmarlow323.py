from typing import Any, Mapping
from unittest.mock import ANY

import pytest
from ophyd_async.core import DeviceCollector, StandardReadable, set_mock_value

from dodal.devices.watsonmarlow323 import WatsonMarlow323, WatsonMarlow323Direction

@pytest.fixture
async def watsonmarlow323() -> WatsonMarlow323:
    async with DeviceCollector(mock=True):
        wm_pump = WatsonMarlow323("DEMO-WMPUMP-01:")

    return wm_pump

async def test_reading_pump_reads_speed_and_direction( watsonmarlow323: WatsonMarlow323):
    set_mock_value(watsonmarlow323.speed, 25)
    set_mock_value(watsonmarlow323.direction, WatsonMarlow323Direction.CCW)
    
    await assert_reading(
        watsonmarlow323,
        {
            "wm_pump-speed": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 25,
            },
            "wm_pump-direction": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": "CCW",
            },
        },
    )

async def assert_reading(
    device: StandardReadable,
    expected_reading: Mapping[str, Any],
) -> None:
    reading = await device.read()

    assert reading == expected_reading
