import asyncio
from unittest.mock import AsyncMock

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices, set_mock_attr
from ophyd_async.epics.motor import Motor
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i05_shared import PolynomCompoundMotors


@pytest.fixture
async def x_motor() -> Motor:
    async with init_devices(mock=True):
        x_motor = Motor("")
    return x_motor


@pytest.fixture
async def y_motor() -> Motor:
    async with init_devices(mock=True):
        y_motor = Motor("")
    return y_motor


@pytest.fixture
async def z_motor() -> Motor:
    async with init_devices(mock=True):
        z_motor = Motor("")
    return z_motor


async def test_compound_initial_values_are_set(x_motor: Motor, y_motor: Motor):
    expected_offset = 2
    expected_step = 1.5
    expected_square = 3
    async with init_devices(mock=True):
        compound = PolynomCompoundMotors(
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
async def compound(x_motor: Motor, y_motor: Motor) -> PolynomCompoundMotors:
    async with init_devices(mock=True):
        compound = PolynomCompoundMotors(x_motor, y_motor)
    return compound


# https://github.com/bluesky/ophyd-async/issues/1471
# async def test_config_includes(compound: PolynomCompoundMotors):
#     await assert_configuration(
#         compound,
#         {
#             "compound-offset": partial_reading(0.0),
#             "compound-step": partial_reading(0.0),
#             "compound-square": partial_reading(0.0),
#             "compound-master_name": partial_reading(compound.master_ref().name),
#             "compound-slave_name": partial_reading(compound.slave_ref().name),
#         },
#     )

# https://github.com/bluesky/ophyd-async/issues/1471
# async def test_compound_change_ref_updates_master_and_slave_name_signal(
#     compound: PolynomCompoundMotors, x_motor: Motor, y_motor: Motor
# ):
#     assert compound.master_ref() == x_motor
#     assert compound.slave_ref() == y_motor

#     master_name, slave_name = await asyncio.gather(
#         compound.master_name.get_value(), compound.slave_name.get_value()
#     )

#     assert master_name == x_motor.name
#     assert slave_name == y_motor.name

#     compound.master_ref = Reference(y_motor)
#     compound.slave_ref = Reference(x_motor)

#     master_name, slave_name = await asyncio.gather(
#         compound.master_name.get_value(), compound.slave_name.get_value()
#     )

#     assert master_name == y_motor.name
#     assert slave_name == x_motor.name


async def test_compound_read(compound: PolynomCompoundMotors):
    await assert_reading(
        compound,
        {
            "x_motor": partial_reading(0.0),
            "y_motor": partial_reading(0.0),
        },
    )


async def test_compound_move(
    compound: PolynomCompoundMotors,
):
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
        compound.master_ref().user_readback.get_value(),
        compound.slave_ref().user_readback.get_value(),
    )
    assert master_val == new_position
    assert slave_val == expected_slave_position


async def test_compound_move_and_locate(
    compound: PolynomCompoundMotors,
    run_engine: RunEngine,
):
    new_position = 1.23

    run_engine(bps.mv(compound, new_position))

    located_position = await compound.locate()

    assert located_position == {
        "setpoint": new_position,
        "readback": new_position,
    }


@pytest.mark.parametrize("success", [True, False])
async def test_compound_stop(compound: PolynomCompoundMotors, success: bool):
    master_mock_stop = AsyncMock()
    slave_mock_stop = AsyncMock()
    set_mock_attr(compound.master_ref(), "stop", master_mock_stop)
    set_mock_attr(compound.slave_ref(), "stop", slave_mock_stop)

    await compound.stop(success)

    master_mock_stop.assert_awaited_once_with(success)
    slave_mock_stop.assert_awaited_once_with(success)
