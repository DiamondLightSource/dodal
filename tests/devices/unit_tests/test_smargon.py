from unittest.mock import call

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices, observe_value
from ophyd_async.testing import get_mock_put, set_mock_value

from dodal.devices.smargon import CombinedMove, DeferMoves, Smargon, StubPosition
from dodal.devices.util.test_utils import patch_motor


@pytest.fixture
async def smargon() -> Smargon:
    async with init_devices(mock=True):
        smargon = Smargon(name="smargon")
    patch_motor(smargon.x)
    patch_motor(smargon.y)
    patch_motor(smargon.z)
    patch_motor(smargon.omega)
    patch_motor(smargon.phi)
    patch_motor(smargon.chi)
    return smargon


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


async def test_given_set_fails_then_defer_moves_turned_back_off(smargon: Smargon):
    class MyException(Exception): ...

    get_mock_put(smargon.x.user_setpoint).side_effect = MyException()
    with pytest.raises(MyException):
        await smargon.set(CombinedMove(x=10))

    get_mock_put(smargon.defer_move).assert_has_calls(
        [call(DeferMoves.ON, wait=True), call(DeferMoves.OFF, wait=True)]
    )
