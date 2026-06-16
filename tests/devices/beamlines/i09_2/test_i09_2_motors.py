from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import DeviceMock, init_devices, set_mock_value
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


@pytest.mark.parametrize(
    "deadband, setpoint, readback, expected_within_threshold",
    (
        (1, 10, 11.1, False),
        (2, 10, 7, False),
        (0.5, 5, 4.9, True),
        (0.1, 100, 100.01, True),
    ),
)
async def test_piezo_motor_within_threshold(
    piezo_motor: PiezoElectricMotor,
    deadband: float,
    setpoint: float,
    readback: float,
    expected_within_threshold: bool,
) -> None:
    # Setup mock to not use default as do not want the setpoint and readback to be the
    # same for tests so we can correctly test threshold signals.
    await piezo_motor.connect(mock=DeviceMock())
    set_mock_value(piezo_motor.deadband, deadband)
    set_mock_value(piezo_motor.user_setpoint, setpoint)
    set_mock_value(piezo_motor.user_readback, readback)

    assert await piezo_motor.within_tolerance.get_value() == expected_within_threshold


async def test_piezo_motor_stop(piezo_motor: PiezoElectricMotor) -> None:
    piezo_motor.motor_stop.set = AsyncMock()
    await piezo_motor.stop()
    piezo_motor.motor_stop.set.assert_awaited_once_with(1)


async def test_piezo_motor_set(piezo_motor: PiezoElectricMotor) -> None:
    await piezo_motor.set(4)
    assert await piezo_motor.user_readback.get_value() == 4
    assert await piezo_motor.user_setpoint.get_value() == 4


async def test_tolerance_logic_move(piezo_motor: PiezoElectricMotor):
    set_mock_value(piezo_motor.movable_logic.readback, 0.0)
    move_task = piezo_motor.movable_logic.move(new_position=10.0, timeout=5.0)
    for value in [2.0, 5.0, 8.0, 9.5, 13.0]:
        set_mock_value(piezo_motor.movable_logic.readback, value)
        assert await piezo_motor.within_tolerance.get_value() is False
    set_mock_value(piezo_motor.movable_logic.readback, 9.91)
    await move_task
    assert await piezo_motor.within_tolerance.get_value() is True
