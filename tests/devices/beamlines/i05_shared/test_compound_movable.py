import asyncio
from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import Reference, StandardMovable, init_devices, set_mock_attr
from ophyd_async.epics.motor import Motor
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.i05_shared import PolynomCompoundMovable


@pytest.fixture
async def x_motor() -> Motor:
    async with init_devices(mock=True):
        x_motor = Motor("TEST:X")
    return x_motor


@pytest.fixture
async def y_motor() -> Motor:
    async with init_devices(mock=True):
        y_motor = Motor("TEST:Y")
    return y_motor


@pytest.fixture
async def z_motor() -> Motor:
    async with init_devices(mock=True):
        z_motor = Motor("TEST:Z")
    return z_motor


async def test_compound_initial_values_are_set(x_motor: Motor, y_motor: Motor):
    expected_offset = 2
    expected_step = 1.5
    expected_square = 3
    async with init_devices(mock=True):
        compound = PolynomCompoundMovable(
            x_motor,
            y_motor,
            offset=expected_offset,
            step=expected_step,
            square=expected_square,
        )

    offset, step, square = await asyncio.gather(
        compound.offset.get_value(),
        compound.step.get_value(),
        compound.square.get_value(),
    )
    assert offset == expected_offset
    assert step == expected_step
    assert square == expected_square


@pytest.fixture
async def compound(x_motor: Motor, y_motor: Motor) -> PolynomCompoundMovable:
    async with init_devices(mock=True):
        compound = PolynomCompoundMovable(x_motor, y_motor)
    return compound


async def test_config_includes(compound: PolynomCompoundMovable):
    await assert_configuration(
        compound,
        {
            "compound-offset": partial_reading(0.0),
            "compound-step": partial_reading(0.0),
            "compound-square": partial_reading(0.0),
            "compound-master_name": partial_reading(compound.master_ref().name),
            "compound-slave_name": partial_reading(compound.slave_ref().name),
        },
    )


async def test_compound_change_ref_updates_master_and_slave_name_signal(
    compound: PolynomCompoundMovable,
    x_motor: StandardMovable[float],
    y_motor: StandardMovable[float],
):
    x_motor_val = 1
    y_motor_val = 2
    await asyncio.gather(x_motor.set(x_motor_val), y_motor.set(y_motor_val))

    assert await compound.readback.get_value() == x_motor_val

    assert compound.master_ref() == x_motor
    assert compound.slave_ref() == y_motor

    master_name, slave_name = await asyncio.gather(
        compound.master_name.get_value(), compound.slave_name.get_value()
    )

    assert master_name == x_motor.name
    assert slave_name == y_motor.name

    compound.master_ref = Reference(y_motor)
    compound.slave_ref = Reference(x_motor)

    expected_master_name, expected_slave_name = await asyncio.gather(
        compound.master_name.get_value(), compound.slave_name.get_value()
    )

    assert y_motor.name == expected_master_name
    assert x_motor.name == expected_slave_name

    # assert await compound.readback.get_value() == y_motor_val


async def test_compound_read(compound: PolynomCompoundMovable):
    await assert_reading(
        compound,
        {
            "compound": partial_reading(0.0),
            "x_motor": partial_reading(0.0),
            "y_motor": partial_reading(0.0),
        },
    )


async def test_compound_move(compound: PolynomCompoundMovable):
    new_position = 10.0
    offset = 1.0
    step = 2.0
    square = 3.0

    await asyncio.gather(
        compound.offset.set(offset),
        compound.step.set(step),
        compound.square.set(square),
    )
    await compound.set(new_position)

    expected_slave_position = offset + step * new_position + square * new_position**2

    master_val, slave_val = await asyncio.gather(
        compound.master_ref().movable_logic.readback.get_value(),
        compound.slave_ref().movable_logic.readback.get_value(),
    )
    assert master_val == new_position
    assert slave_val == expected_slave_position


async def test_compound_stop(compound: PolynomCompoundMovable):
    master_mock_stop = AsyncMock()
    slave_mock_stop = AsyncMock()
    set_mock_attr(compound.master_ref(), "stop", master_mock_stop)
    set_mock_attr(compound.slave_ref(), "stop", slave_mock_stop)

    await compound.stop()

    master_mock_stop.assert_awaited_once()
    slave_mock_stop.assert_awaited_once()
