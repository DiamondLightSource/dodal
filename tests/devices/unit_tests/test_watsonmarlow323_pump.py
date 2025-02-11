from unittest.mock import ANY

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, set_mock_value

from dodal.devices.watsonmarlow323_pump import (
    WatsonMarlow323Pump,
    WatsonMarlow323PumpDirection,
    WatsonMarlow323PumpState,
)


@pytest.fixture
async def watsonmarlow323() -> WatsonMarlow323Pump:
    async with init_devices(mock=True):
        wm_pump = WatsonMarlow323Pump("DEMO-WMPUMP-01:")

    return wm_pump


async def test_reading_pump_reads_state_speed_and_direction(
    watsonmarlow323: WatsonMarlow323Pump,
):
    set_mock_value(watsonmarlow323.state, WatsonMarlow323PumpState.STOPPED)
    set_mock_value(watsonmarlow323.speed, 25)
    set_mock_value(watsonmarlow323.direction, WatsonMarlow323PumpDirection.CLOCKWISE)

    await assert_reading(
        watsonmarlow323,
        {
            "wm_pump-state": {
                "value": WatsonMarlow323PumpState.STOPPED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "wm_pump-speed": {
                "value": 25,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "wm_pump-direction": {
                "value": WatsonMarlow323PumpDirection.CLOCKWISE,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )
