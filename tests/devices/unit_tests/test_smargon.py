from time import sleep

from dodal.devices.smargon import Smargon, StubPosition
from dodal.testing_utils import set_smargon_pos


def test_given_to_robot_disp_low_when_stub_offsets_set_to_robot_load_then_proc_set(
    mock_smargon: Smargon,
):
    mock_smargon.stub_offsets.to_robot_load.disp.sim_put(0)  # type: ignore

    status = mock_smargon.stub_offsets.set(StubPosition.RESET_TO_ROBOT_LOAD)
    status.wait()

    assert mock_smargon.stub_offsets.to_robot_load.proc.get() == 1
    assert mock_smargon.stub_offsets.center_at_current_position.proc.get() == 0


def test_given_center_disp_low_and_at_centre_when_stub_offsets_set_to_center_then_proc_set(
    mock_smargon: Smargon,
):
    mock_smargon.stub_offsets.center_at_current_position.disp.sim_put(0)  # type: ignore
    set_smargon_pos(mock_smargon, (0, 0, 0))

    status = mock_smargon.stub_offsets.set(StubPosition.CURRENT_AS_CENTER)
    status.wait()

    assert mock_smargon.stub_offsets.to_robot_load.proc.get() == 0
    assert mock_smargon.stub_offsets.center_at_current_position.proc.get() == 1


def test_given_center_disp_low_when_stub_offsets_set_to_center_and_moved_to_0_0_0_then_proc_set(
    mock_smargon: Smargon,
):
    mock_smargon.stub_offsets.center_at_current_position.disp.sim_put(0)  # type: ignore

    set_smargon_pos(mock_smargon, (1.5, 0.5, 3.4))

    status = mock_smargon.stub_offsets.set(StubPosition.CURRENT_AS_CENTER)

    sleep(0.01)

    assert mock_smargon.stub_offsets.center_at_current_position.proc.get() == 1

    assert not status.done

    set_smargon_pos(mock_smargon, (0, 0, 0))

    status.wait()

    assert mock_smargon.stub_offsets.to_robot_load.proc.get() == 0
    assert mock_smargon.stub_offsets.center_at_current_position.proc.get() == 1
