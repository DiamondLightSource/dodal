from unittest.mock import ANY, AsyncMock

import pytest
from bluesky import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.turbo_slit import TurboSlit


@pytest.fixture
def slit() -> TurboSlit:
    with init_devices(mock=True):
        slit = TurboSlit(prefix="TEST-EA-TURBOSLIT:", name="turbo_slit")
    return slit


async def test_turbo_slit_set(slit: TurboSlit, RE: RunEngine):
    set_mock_value(slit.xfine.user_readback, 0.0)
    await slit.set(0.5)
    assert slit.xfine.set.call_count == 1
    assert slit.xfine.set.call_args == AsyncMock.call(0.5)


async def test_turbo_slit_read(slit: TurboSlit):
    set_mock_value(slit.gap.user_readback, 0.5)
    set_mock_value(slit.arc.user_readback, 1.0)
    set_mock_value(slit.xfine.user_readback, 1.5)

    reading = await slit.read()

    assert reading == {
        "turbo_slit-gap": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.5,
        },
        "turbo_slit-arc": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 1.0,
        },
        "turbo_slit-xfine": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 1.5,
        },
    }
