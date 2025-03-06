from unittest.mock import ANY

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.linkam3 import Linkam3


@pytest.fixture
async def fake_linkam():
    async with init_devices(mock=True):
        fake_linkam: Linkam3 = Linkam3("", "linkam")

    def set_temp(value: float, *args, **kwargs):
        set_mock_value(fake_linkam.temp, value)

    callback_on_mock_put(fake_linkam.set_point, set_temp)
    return fake_linkam


async def test_linkam_bits_all_init_at_false(fake_linkam: Linkam3):
    assert not await fake_linkam.in_error()
    assert not await fake_linkam.at_setpoint()
    assert not await fake_linkam.heater_on()
    assert not await fake_linkam.pump_on()
    assert not await fake_linkam.pump_auto()


async def test_linkam_temp_and_setpoint_init_at_0(fake_linkam: Linkam3):
    assert await fake_linkam.locate() == {
        "readback": 0.0,
        "setpoint": 0.0,
    }


async def test_linkam_locate_returns_temp_and_setpoint_values(fake_linkam: Linkam3):
    readback = await fake_linkam.temp.get_value()
    setpoint = await fake_linkam.set_point.get_value()
    locate = await fake_linkam.locate()

    assert locate == {
        "readback": readback,
        "setpoint": setpoint,
    }


async def test_linkam_set_changes_setpoint_and_temp(fake_linkam: Linkam3):
    assert await fake_linkam.locate() == {
        "readback": 0.0,
        "setpoint": 0.0,
    }
    # move
    await fake_linkam.set(1.0, 1.0)

    mock_put = get_mock_put(fake_linkam.set_point)
    mock_put.assert_called_once_with(1.0, wait=ANY)
    assert await fake_linkam.locate() == {
        "readback": 1.0,
        "setpoint": 1.0,
    }
