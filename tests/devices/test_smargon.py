from collections.abc import AsyncGenerator
from unittest.mock import MagicMock, call

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices, observe_value
from ophyd_async.epics.motor import MotorLimitsException
from ophyd_async.testing import get_mock_put, set_mock_value

from dodal.devices.smargon import CombinedMove, DeferMoves, Smargon, StubPosition
from dodal.testing import patch_all_motors


@pytest.fixture
async def smargon() -> AsyncGenerator[Smargon]:
    async with init_devices(mock=True):
        smargon = Smargon("")
    with patch_all_motors(smargon):
        yield smargon


def set_smargon_pos(smargon: Smargon, pos: tuple[float, float, float]):
    set_mock_value(smargon.x.user_readback, pos[0])
    set_mock_value(smargon.y.user_readback, pos[1])
    set_mock_value(smargon.z.user_readback, pos[2])


async def test_given_to_robot_disp_low_when_stub_offsets_set_to_robot_load_then_proc_set(
    RE: RunEngine,
    smargon: Smargon,
):
    set_mock_value(smargon.stub_offsets.to_robot_load.disp, 0)

    def plan():
        yield from bps.abs_set(
            smargon.stub_offsets, StubPosition.RESET_TO_ROBOT_LOAD, wait=True
        )
        robot_load_proc = yield from bps.rd(smargon.stub_offsets.to_robot_load.proc)
        assert robot_load_proc == 1
        current_pos_proc = yield from bps.rd(
            smargon.stub_offsets.center_at_current_position.proc
        )
        assert current_pos_proc == 0

    RE(plan())


async def test_given_center_disp_low_and_at_centre_when_stub_offsets_set_to_center_then_proc_set(
    RE: RunEngine,
    smargon: Smargon,
):
    set_mock_value(smargon.stub_offsets.center_at_current_position.disp, 0)
    set_smargon_pos(smargon, (0, 0, 0))

    def plan():
        yield from bps.abs_set(
            smargon.stub_offsets, StubPosition.CURRENT_AS_CENTER, wait=True
        )
        assert (yield from bps.rd(smargon.stub_offsets.to_robot_load.proc)) == 0
        assert (
            yield from bps.rd(smargon.stub_offsets.center_at_current_position.proc)
        ) == 1

    RE(plan())


async def test_given_center_disp_low_when_stub_offsets_set_to_center_and_moved_to_0_0_0_then_proc_set(
    smargon: Smargon,
):
    set_mock_value(smargon.stub_offsets.center_at_current_position.disp, 0)

    set_smargon_pos(smargon, (1.5, 0.5, 3.4))

    current_proc_values = observe_value(
        smargon.stub_offsets.center_at_current_position.proc
    )
    assert await anext(current_proc_values) == 0

    status = smargon.stub_offsets.set(StubPosition.CURRENT_AS_CENTER)

    assert await anext(current_proc_values) == 1

    assert not status.done

    set_smargon_pos(smargon, (0, 0, 0))

    assert await smargon.stub_offsets.to_robot_load.proc.get_value() == 0


@pytest.mark.parametrize(
    "test_x, test_y, test_z, test_omega, test_chi, test_phi",
    [
        (2000, 20, 30, 5, 15, 25),  # x goes beyond upper limit
        (-2000, 20, 30, 5, 15, 25),  # x goes beyond lower limit
        (10, 2000, 30, 5, 15, 25),  # y goes beyond upper limit
        (10, -2000, 30, 5, 15, 25),  # y goes beyond lower limit
        (10, 20, 2000, 5, 15, 25),  # z goes beyond upper limit
        (10, 20, -2000, 5, 15, 25),  # z goes beyond lower limit
        (10, 20, 30, 2000, 15, 25),  # omega goes beyond upper limit
        (10, 20, 30, -2000, 15, 25),  # omega goes beyond lower limit
        (10, 20, 30, 5, 2000, 25),  # chi goes beyond upper limit
        (10, 20, 30, 5, -2000, 25),  # chi goes beyond lower limit
        (10, 20, 30, 5, 15, 2000),  # phi goes beyond upper limit
        (10, 20, 30, 5, 15, -2000),  # phi goes beyond lower limit
    ],
)
async def test_given_set_with_value_outside_motor_limit(
    smargon: Smargon, test_x, test_y, test_z, test_omega, test_chi, test_phi
):
    set_mock_value(smargon.x.low_limit_travel, -1999)
    set_mock_value(smargon.y.low_limit_travel, -1999)
    set_mock_value(smargon.z.low_limit_travel, -1999)
    set_mock_value(smargon.omega.low_limit_travel, -1999)
    set_mock_value(smargon.chi.low_limit_travel, -1999)
    set_mock_value(smargon.phi.low_limit_travel, -1999)
    set_mock_value(smargon.x.high_limit_travel, 1999)
    set_mock_value(smargon.y.high_limit_travel, 1999)
    set_mock_value(smargon.z.high_limit_travel, 1999)
    set_mock_value(smargon.omega.high_limit_travel, 1999)
    set_mock_value(smargon.chi.high_limit_travel, 1999)
    set_mock_value(smargon.phi.high_limit_travel, 1999)

    with pytest.raises(MotorLimitsException):
        await smargon.set(
            CombinedMove(
                x=test_x,
                y=test_y,
                z=test_z,
                omega=test_omega,
                chi=test_chi,
                phi=test_phi,
            )
        )


async def test_given_set_with_single_value_then_that_motor_moves(smargon: Smargon):
    await smargon.set(CombinedMove(x=10))

    get_mock_put(smargon.x.user_setpoint).assert_called_once_with(10, wait=True)
    get_mock_put(smargon.defer_move).assert_has_calls(
        [call(DeferMoves.ON, wait=True), call(DeferMoves.OFF, wait=True)]
    )


async def test_given_set_with_none_then_that_motor_does_not_move(smargon: Smargon):
    await smargon.set(CombinedMove(x=10, y=None))

    get_mock_put(smargon.x.user_setpoint).assert_called_once_with(10, wait=True)
    get_mock_put(smargon.y.user_setpoint).assert_not_called()
    get_mock_put(smargon.defer_move).assert_has_calls(
        [call(DeferMoves.ON, wait=True), call(DeferMoves.OFF, wait=True)]
    )


async def test_given_set_with_all_values_then_motors_move(smargon: Smargon):
    await smargon.set(CombinedMove(x=10, y=20, z=30, omega=5, chi=15, phi=25))

    get_mock_put(smargon.x.user_setpoint).assert_called_once_with(10, wait=True)
    get_mock_put(smargon.y.user_setpoint).assert_called_once_with(20, wait=True)
    get_mock_put(smargon.z.user_setpoint).assert_called_once_with(30, wait=True)
    get_mock_put(smargon.omega.user_setpoint).assert_called_once_with(5, wait=True)
    get_mock_put(smargon.chi.user_setpoint).assert_called_once_with(15, wait=True)
    get_mock_put(smargon.phi.user_setpoint).assert_called_once_with(25, wait=True)

    get_mock_put(smargon.defer_move).assert_has_calls(
        [call(DeferMoves.ON, wait=True), call(DeferMoves.OFF, wait=True)]
    )


async def test_given_set_with_all_values_then_motors_set_in_order(smargon: Smargon):
    parent = MagicMock()
    parent.attach_mock(get_mock_put(smargon.defer_move), "defer_move")
    parent.attach_mock(get_mock_put(smargon.x.user_setpoint), "x")
    parent.attach_mock(get_mock_put(smargon.y.user_setpoint), "y")
    parent.attach_mock(get_mock_put(smargon.z.user_setpoint), "z")
    parent.attach_mock(get_mock_put(smargon.omega.user_setpoint), "omega")
    parent.attach_mock(get_mock_put(smargon.chi.user_setpoint), "chi")
    parent.attach_mock(get_mock_put(smargon.phi.user_setpoint), "phi")

    await smargon.set(CombinedMove(x=10, y=20, z=30, omega=5, chi=15, phi=25))

    assert len(parent.mock_calls) == 8
    assert parent.mock_calls[0] == call.defer_move(DeferMoves.ON, wait=True)
    parent.assert_has_calls(
        [
            call.x(10, wait=True),
            call.y(20, wait=True),
            call.z(30, wait=True),
            call.omega(5, wait=True),
            call.chi(15, wait=True),
            call.phi(25, wait=True),
        ],
        any_order=True,
    )
    assert parent.mock_calls[-1] == call.defer_move(DeferMoves.OFF, wait=True)


async def test_given_set_fails_then_defer_moves_turned_back_off(smargon: Smargon):
    class MyException(Exception): ...

    smargon.x.user_setpoint.set = MagicMock(side_effect=MyException())
    with pytest.raises(MyException):
        await smargon.set(CombinedMove(x=10))

    get_mock_put(smargon.defer_move).assert_has_calls(
        [call(DeferMoves.ON, wait=True), call(DeferMoves.OFF, wait=True)]
    )


async def test_given_motor_does_not_change_setpoint_then_deferred_move_times_out(
    smargon: Smargon,
):
    smargon.DEFERRED_MOVE_SET_TIMEOUT = 0.01  # type: ignore

    # Override the callback so it doesn't change the `user_setpoint`
    smargon.x.user_setpoint.set = MagicMock()

    with pytest.raises(TimeoutError):
        await smargon.set(CombinedMove(x=10))
