from collections.abc import AsyncGenerator
from unittest.mock import MagicMock, call

import pytest
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.epics.motor import MotorLimitsError

from dodal.devices.beamlines.i15_1.hexapod import CombinedMove, Hexapod
from dodal.devices.defered_move_utils import DeferMoves


@pytest.fixture
async def hexapod() -> AsyncGenerator[Hexapod]:
    async with init_devices(mock=True):
        hexapod = Hexapod("", "")
    yield hexapod


@pytest.mark.parametrize(
    "test_x, test_y, test_z, test_rx, test_ry, test_rz",
    [
        (2000, 20, 30, 15, 25, 35),  # x goes beyond upper limit
        (-2000, 20, 30, 15, 25, 35),  # x goes beyond lower limit
        (10, 2000, 30, 15, 25, 35),  # y goes beyond upper limit
        (10, -2000, 30, 15, 25, 35),  # y goes beyond lower limit
        (10, 20, 2000, 15, 25, 35),  # z goes beyond upper limit
        (10, 20, -2000, 15, 25, 35),  # z goes beyond lower limit
        (10, 20, 30, 2000, 25, 35),  # rx goes beyond upper limit
        (10, 20, 30, -2000, 25, 35),  # rx goes beyond lower limit
        (10, 20, 30, 15, 2000, 35),  # ry goes beyond upper limit
        (10, 20, 30, 15, -2000, 35),  # ry goes beyond lower limit
        (10, 20, 30, 15, 25, 2000),  # rz goes beyond upper limit
        (10, 20, 30, 15, 25, -2000),  # rz goes beyond lower limit
    ],
)
async def test_given_set_with_value_outside_motor_limit(
    hexapod: Hexapod, test_x, test_y, test_z, test_rx, test_ry, test_rz
):
    for motor in [
        hexapod.x,
        hexapod.y,
        hexapod.z,
        hexapod.rx,
        hexapod.ry,
        hexapod.rz,
    ]:
        set_mock_value(motor.low_limit_travel, -1999)
        set_mock_value(motor.high_limit_travel, 1999)
        set_mock_value(motor.dial_low_limit_travel, -1999)
        set_mock_value(motor.dial_high_limit_travel, 1999)

    with pytest.raises(MotorLimitsError):
        await hexapod.set(
            CombinedMove(
                x=test_x,
                y=test_y,
                z=test_z,
                rx=test_rx,
                ry=test_ry,
                rz=test_rz,
            )
        )


async def test_given_set_with_single_value_then_that_motor_moves(hexapod: Hexapod):
    await hexapod.set(CombinedMove(x=10))

    get_mock_put(hexapod.x.user_setpoint).assert_called_once_with(10)
    get_mock_put(hexapod.defer_move).assert_has_calls(
        [call(DeferMoves.ON), call(DeferMoves.OFF)]
    )


async def test_given_set_with_none_then_that_motor_does_not_move(hexapod: Hexapod):
    await hexapod.set(CombinedMove(x=10, y=None))

    get_mock_put(hexapod.x.user_setpoint).assert_called_once_with(10)
    get_mock_put(hexapod.y.user_setpoint).assert_not_called()
    get_mock_put(hexapod.defer_move).assert_has_calls(
        [call(DeferMoves.ON), call(DeferMoves.OFF)]
    )


async def test_given_set_with_all_values_then_motors_move(hexapod: Hexapod):
    await hexapod.set(CombinedMove(x=10, y=20, z=30, rx=15, ry=25, rz=35))

    get_mock_put(hexapod.x.user_setpoint).assert_called_once_with(10)
    get_mock_put(hexapod.y.user_setpoint).assert_called_once_with(20)
    get_mock_put(hexapod.z.user_setpoint).assert_called_once_with(30)
    get_mock_put(hexapod.rx.user_setpoint).assert_called_once_with(15)
    get_mock_put(hexapod.ry.user_setpoint).assert_called_once_with(25)
    get_mock_put(hexapod.rz.user_setpoint).assert_called_once_with(35)

    get_mock_put(hexapod.defer_move).assert_has_calls(
        [call(DeferMoves.ON), call(DeferMoves.OFF)]
    )


async def test_given_set_with_all_values_then_motors_set_in_order(hexapod: Hexapod):
    parent = MagicMock()
    parent.attach_mock(get_mock_put(hexapod.defer_move), "defer_move")
    parent.attach_mock(get_mock_put(hexapod.x.user_setpoint), "x")
    parent.attach_mock(get_mock_put(hexapod.y.user_setpoint), "y")
    parent.attach_mock(get_mock_put(hexapod.z.user_setpoint), "z")
    parent.attach_mock(get_mock_put(hexapod.rx.user_setpoint), "rx")
    parent.attach_mock(get_mock_put(hexapod.ry.user_setpoint), "ry")
    parent.attach_mock(get_mock_put(hexapod.rz.user_setpoint), "rz")

    await hexapod.set(CombinedMove(x=10, y=20, z=30, rx=15, ry=25, rz=35))

    assert len(parent.mock_calls) == 8
    parent.assert_has_calls(
        [
            call.defer_move(DeferMoves.ON),
            call.x(10),
            call.y(20),
            call.z(30),
            call.rx(15),
            call.ry(25),
            call.rz(35),
            call.defer_move(DeferMoves.OFF),
        ],
    )


async def test_given_set_fails_then_defer_moves_turned_back_off(hexapod: Hexapod):
    class MyError(Exception): ...

    hexapod.x.user_setpoint.set = MagicMock(side_effect=MyError())
    with pytest.raises(MyError):
        await hexapod.set(CombinedMove(x=10))

    get_mock_put(hexapod.defer_move).assert_has_calls(
        [call(DeferMoves.ON), call(DeferMoves.OFF)]
    )


async def test_given_motor_does_not_change_setpoint_then_deferred_move_times_out(
    hexapod: Hexapod,
):
    hexapod.DEFERRED_MOVE_SET_TIMEOUT = 0.01  # type: ignore

    # Override the callback so it doesn't change the `user_setpoint`
    hexapod.x.user_setpoint.set = MagicMock()

    with pytest.raises(TimeoutError):
        await hexapod.set(CombinedMove(x=10))
