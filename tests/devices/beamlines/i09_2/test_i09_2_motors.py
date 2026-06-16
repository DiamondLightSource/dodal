from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i09_2 import (
    I092SampleManipulator,
    PiezoElectricMotor,
)


@pytest.fixture
def sm() -> I092SampleManipulator:
    with init_devices(mock=True):
        sm = I092SampleManipulator("TEST:")
    return sm


async def test_sm_read(sm: I092SampleManipulator) -> None:
    await assert_reading(
        sm,
        {
            "sm-x1": partial_reading(0),
            "sm-x2": partial_reading(0),
            "sm-x3": partial_reading(0),
            "sm-y": partial_reading(0),
            "sm-z1": partial_reading(0),
            "sm-z2": partial_reading(0),
            "sm-xc": partial_reading(0),
            "sm-zc": partial_reading(0),
        },
    )


@pytest.fixture
async def piezo_motor() -> PiezoElectricMotor:
    with init_devices(mock=True):
        piezo_motor = PiezoElectricMotor("TEST:")
    return piezo_motor


async def test_piezo_motor_stop(piezo_motor: PiezoElectricMotor) -> None:
    piezo_motor.motor_stop.set = AsyncMock()
    await piezo_motor.stop()
    piezo_motor.motor_stop.set.assert_awaited_once_with(1)


async def test_piezo_motor_set(piezo_motor: PiezoElectricMotor) -> None:
    await piezo_motor.set(4)
    assert await piezo_motor.user_readback.get_value() == 4
    assert await piezo_motor.user_setpoint.get_value() == 4
