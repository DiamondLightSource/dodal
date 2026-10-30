import asyncio
from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import init_devices, set_mock_attr
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
            "compound-master_name": partial_reading("x_motor"),
            "compound-slave_name": partial_reading("y_motor"),
        },
    )


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
        compound._master_ref().movable_logic.readback.get_value(),
        compound._slave_ref().movable_logic.readback.get_value(),
    )
    assert master_val == new_position
    assert slave_val == expected_slave_position


async def test_compound_stop(compound: PolynomCompoundMovable):
    master_mock_stop = AsyncMock()
    slave_mock_stop = AsyncMock()
    set_mock_attr(compound._master_ref(), "stop", master_mock_stop)
    set_mock_attr(compound._slave_ref(), "stop", slave_mock_stop)

    await compound.stop()

    master_mock_stop.assert_awaited_once()
    slave_mock_stop.assert_awaited_once()
