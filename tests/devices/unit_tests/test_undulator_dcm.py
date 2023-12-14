from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from ophyd.sim import make_fake_device
from ophyd.status import Status

from dodal.devices.DCM import DCM
from dodal.devices.undulator import Undulator, UndulatorGapAccess
from dodal.devices.undulator_dcm import (
    AccessError,
    UndulatorDCM,
    _get_closest_gap_for_energy,
    _get_energy_distance_table,
)


@pytest.fixture
def fake_undulator_dcm() -> UndulatorDCM:
    undulator: Undulator = make_fake_device(Undulator)(
        name="undulator",
        lookup_table_path="./tests/devices/unit_tests/test_beamline_undulator_to_gap_lookup_table.txt",
    )
    dcm: DCM = make_fake_device(DCM)(name="dcm")
    undulator_dcm: UndulatorDCM = make_fake_device(UndulatorDCM)(
        undulator, dcm, name="undulator_dcm"
    )
    return undulator_dcm


def test_when_gap_access_is_disabled_set_energy_then_error_is_raised(
    fake_undulator_dcm: UndulatorDCM,
):
    fake_undulator_dcm.undulator.gap_access.sim_put(UndulatorGapAccess.DISABLED.value)  # type: ignore
    with pytest.raises(AccessError):
        fake_undulator_dcm.energy_kev.set(5)


def test_energy_to_distance_table_correct_format(fake_undulator_dcm: UndulatorDCM):
    table = _get_energy_distance_table(fake_undulator_dcm.undulator.lookup_table_path)
    assert table[0][0] == 5700
    assert table[49][1] == 6.264
    assert table.shape == (50, 2)


@pytest.mark.parametrize(
    "dcm_energy, expected_output", [(5730, 5.4606), (7200, 6.045), (9000, 6.404)]
)
def test_correct_closest_distance_to_energy_from_table(dcm_energy, expected_output):
    energy_to_distance_table = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])
    assert (
        _get_closest_gap_for_energy(dcm_energy, energy_to_distance_table)
        == expected_output
    )


@patch("dodal.devices.undulator_dcm.loadtxt")
@patch("dodal.devices.undulator_dcm.LOGGER")
def test_if_gap_is_wrong_then_logger_info_is_called_and_gap_is_set_correctly(
    mock_logger: MagicMock, mock_load: MagicMock, fake_undulator_dcm: UndulatorDCM
):
    fake_undulator_dcm.undulator.current_gap.sim_put(5.3)  # type: ignore
    fake_undulator_dcm.undulator.gap_motor.move = MagicMock()
    fake_undulator_dcm.dcm.energy_in_kev.move = MagicMock()
    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])
    fake_undulator_dcm.dcm.energy_in_kev.user_readback.sim_put(5700)  # type: ignore
    fake_undulator_dcm.energy_kev.set(6900)
    fake_undulator_dcm.dcm.energy_in_kev.move.assert_called_once_with(6900, timeout=10)
    fake_undulator_dcm.undulator.gap_motor.move.assert_called_once_with(
        6.045, timeout=10
    )
    mock_logger.info.assert_called()


@patch("dodal.devices.undulator_dcm.loadtxt")
@patch("dodal.devices.undulator_dcm.LOGGER")
def test_if_gap_is_already_correct_then_dont_move_gap(
    mock_logger: MagicMock, mock_load: MagicMock, fake_undulator_dcm: UndulatorDCM
):
    fake_undulator_dcm.undulator.gap_motor.move = MagicMock()
    fake_undulator_dcm.dcm.energy_in_kev.move = MagicMock()
    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])
    fake_undulator_dcm.undulator.current_gap.sim_put(5.4605)  # type: ignore
    fake_undulator_dcm.energy_kev.set(5800).wait(timeout=0.01)
    fake_undulator_dcm.undulator.gap_motor.move.assert_not_called()
    mock_logger.info.assert_called_once()


def test_energy_set_only_complete_when_all_statuses_are_finished(
    fake_undulator_dcm: UndulatorDCM,
):
    dcm_energy_move_status = Status()
    undulator_gap_move_status = Status()

    fake_undulator_dcm.dcm.energy_in_kev.move = MagicMock(
        return_value=dcm_energy_move_status
    )
    fake_undulator_dcm.undulator.gap_motor.move = MagicMock(
        return_value=undulator_gap_move_status
    )
    _get_energy_distance_table = MagicMock()
    _get_closest_gap_for_energy = MagicMock(return_value=10)
    fake_undulator_dcm.undulator.current_gap.sim_put(5)  # type: ignore
    status: Status = fake_undulator_dcm.energy_kev.set(5800)
    assert not status.success
    dcm_energy_move_status.set_finished()
    assert not status.success
    undulator_gap_move_status.set_finished()
    status.wait(timeout=0.01)
