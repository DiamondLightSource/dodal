from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading

from dodal.devices.motors import SixAxisGonio


@pytest.fixture
def six_axis_gonio(RE: RunEngine):
    with init_devices(mock=True):
        gonio = SixAxisGonio("")

    return gonio


async def test_reading_six_axis_gonio(six_axis_gonio: SixAxisGonio):
    await assert_reading(
        six_axis_gonio,
        {
            "gonio-omega": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-kappa": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-phi": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-z": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-y": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "gonio-x": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )
