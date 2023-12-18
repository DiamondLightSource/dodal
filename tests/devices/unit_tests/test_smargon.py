from time import sleep
from typing import Tuple

import pytest
from ophyd.sim import make_fake_device

from dodal.devices.smargon import Smargon, StubPosition


@pytest.fixture
def smargon() -> Smargon:
    return make_fake_device(Smargon)(name="smargon")


def set_smargon_pos(smargon: Smargon, pos: Tuple[float, float, float]):
    smargon.x.user_readback.sim_put(pos[0])  # type: ignore
    smargon.y.user_readback.sim_put(pos[1])  # type: ignore
    smargon.z.user_readback.sim_put(pos[2])  # type: ignore


def test_given_to_robot_disp_low_when_stub_offsets_set_to_robot_load_then_proc_set(
    smargon: Smargon,
):
    smargon.stub_offsets.to_robot_load.disp.sim_put(0)  # type: ignore

    status = smargon.stub_offsets.set(StubPosition.RESET_TO_ROBOT_LOAD)
    status.wait()

    assert smargon.stub_offsets.to_robot_load.proc.get() == 1
    assert smargon.stub_offsets.center_at_current_position.proc.get() == 0


def test_given_center_disp_low_and_at_centre_when_stub_offsets_set_to_center_then_proc_set(
    smargon: Smargon,
):
    smargon.stub_offsets.center_at_current_position.disp.sim_put(0)  # type: ignore
    set_smargon_pos(smargon, (0, 0, 0))

    status = smargon.stub_offsets.set(StubPosition.CURRENT_AS_CENTER)
    status.wait()

    assert smargon.stub_offsets.to_robot_load.proc.get() == 0
    assert smargon.stub_offsets.center_at_current_position.proc.get() == 1


def test_given_center_disp_low_when_stub_offsets_set_to_center_and_moved_to_0_0_0_then_proc_set(
    smargon: Smargon,
):
    smargon.stub_offsets.center_at_current_position.disp.sim_put(0)  # type: ignore

    set_smargon_pos(smargon, (1.5, 0.5, 3.4))

    status = smargon.stub_offsets.set(StubPosition.CURRENT_AS_CENTER)

    sleep(0.01)

    assert smargon.stub_offsets.center_at_current_position.proc.get() == 1

    assert not status.done

    set_smargon_pos(smargon, (0, 0, 0))

    status.wait()

    assert smargon.stub_offsets.to_robot_load.proc.get() == 0
    assert smargon.stub_offsets.center_at_current_position.proc.get() == 1
