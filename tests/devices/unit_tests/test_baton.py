from unittest.mock import ANY

from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading

from dodal.devices.baton import Baton


async def test_mock_baton_can_be_initialised_and_read(RE: RunEngine):
    with init_devices(mock=True):
        baton = Baton("")
    await assert_reading(
        baton,
        {
            "baton-current_user": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": "",
            },
            "baton-requested_user": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": "",
            },
        },
    )
