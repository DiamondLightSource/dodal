import asyncio
from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import init_devices, set_mock_attr
from ophyd_async.epics.motor import Motor
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.i05_shared import PolynomialCompoundMovable


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


async def test_poly_compound_initial_values_are_set(x_motor: Motor, y_motor: Motor):
    expected_offset = 2
    expected_step = 1.5
    expected_square = 3
    async with init_devices(mock=True):
        poly_compound = PolynomialCompoundMovable(
            x_motor,
            y_motor,
            offset=expected_offset,
            step=expected_step,
            square=expected_square,
        )

    offset, step, square = await asyncio.gather(
        poly_compound.offset.get_value(),
        poly_compound.step.get_value(),
        poly_compound.square.get_value(),
    )
    assert offset == expected_offset
    assert step == expected_step
    assert square == expected_square


@pytest.fixture
async def poly_compound(x_motor: Motor, y_motor: Motor) -> PolynomialCompoundMovable:
    async with init_devices(mock=True):
        poly_compound = PolynomialCompoundMovable(x_motor, y_motor)
    return poly_compound


async def test_poly_compound_config_includes(poly_compound: PolynomialCompoundMovable):
    await assert_configuration(
        poly_compound,
        {
            "poly_compound-offset": partial_reading(0.0),
            "poly_compound-step": partial_reading(0.0),
            "poly_compound-square": partial_reading(0.0),
            "poly_compound-master_name": partial_reading("x_motor"),
            "poly_compound-slave_name": partial_reading("y_motor"),
        },
    )


async def test_poly_compound_read(poly_compound: PolynomialCompoundMovable):
    await assert_reading(
        poly_compound,
        {
            "poly_compound": partial_reading(0.0),
            "x_motor": partial_reading(0.0),
            "y_motor": partial_reading(0.0),
        },
    )


async def test_poly_compound_move(poly_compound: PolynomialCompoundMovable):
    new_position = 10.0
    offset = 1.0
    step = 2.0
    square = 3.0

    await asyncio.gather(
        poly_compound.offset.set(offset),
        poly_compound.step.set(step),
        poly_compound.square.set(square),
    )
    await poly_compound.set(new_position)

    expected_slave_position = offset + step * new_position + square * new_position**2

    master_val, slave_val = await asyncio.gather(
        poly_compound._master_ref().movable_logic.readback.get_value(),
        poly_compound._slave_ref().movable_logic.readback.get_value(),
    )
    assert master_val == new_position
    assert slave_val == expected_slave_position


async def test_poly_compound_stop(poly_compound: PolynomialCompoundMovable):
    master_mock_stop = AsyncMock()
    slave_mock_stop = AsyncMock()
    set_mock_attr(poly_compound._master_ref(), "stop", master_mock_stop)
    set_mock_attr(poly_compound._slave_ref(), "stop", slave_mock_stop)

    await poly_compound.stop()

    master_mock_stop.assert_awaited_once()
    slave_mock_stop.assert_awaited_once()
