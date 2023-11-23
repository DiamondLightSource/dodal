from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from ophyd.sim import make_fake_device

from dodal.devices.DCM import DCM
from dodal.devices.undulator import Undulator, UndulatorGapAccess
from dodal.devices.undulator_dcm import (
    AccessError,
    UndulatorDCM,
    _get_closest_gap_to_dcm_energy,
)


@pytest.fixture
def fake_undulator_dcm() -> UndulatorDCM:
    undulator: Undulator = make_fake_device(Undulator)(
        name="undulator", lookup_table_path=""
    )
    dcm: DCM = make_fake_device(DCM)(name="dcm")
    undulator_dcm: UndulatorDCM = make_fake_device(UndulatorDCM)(
        undulator, dcm, name="undulator_dcm"
    )
    return undulator_dcm


@patch("dodal.devices.undulator_dcm.LOGGER")
def test_when_gap_access_is_disabled_set_energy_returns_and_logs_error(
    mock_logger, fake_undulator_dcm: UndulatorDCM
):
    fake_undulator_dcm.undulator.gap_access.sim_put(UndulatorGapAccess.DISABLED.value)
    with pytest.raises(AccessError):
        fake_undulator_dcm.energy.set(5)

    mock_logger.error.assert_called_once()


@pytest.fixture
def create_energy_distance_table(path):
    # Create lookup text file similar to the lookup table we see on I03
    with open(path, mode="a") as file:
        file.write(
            "#test file\n\
            Units    eV    mm\n\
            5700    5.4606\n\
            14000   5.674\n\
            6000    5.681"
        )


# do we still need a test for this?
# def test_energy_to_distance_table_correct_format(fake_undulator: Undulator, tmp_path):
#     path = f"{tmp_path}/lookup.txt"
#     create_energy_distance_table(path)
#     table = _get_energy_to_distance_table(path)
#     assert table[5700] == 5.4606
#     assert table[14000] == 5.674
#     assert table[6000] == 5.681


@pytest.mark.parametrize(
    "dcm_energy, expected_output", [(5730, 5.4606), (6505, 6.045), (7010, 6.404)]
)
def test_correct_closest_distance_to_energy_from_table(dcm_energy, expected_output):
    energy_to_distance_table = np.array(
        [[5700, 5760, 6000, 6500, 7000], [5.4606, 5.5, 5.681, 6.045, 6.404]]
    )
    assert (
        _get_closest_gap_to_dcm_energy(dcm_energy, energy_to_distance_table)
        == expected_output
    )


@patch("dodal.devices.undulator_dcm.loadtxt")
@patch("dodal.device.undulator_dcm.LOGGER")
def test_if_gap_is_wrong_then_logger_info_and_gap_is_set_correctly(
    mock_logger: MagicMock, mock_load: MagicMock, fake_undulator_dcm
):
    fake_undulator_dcm.undulator.current_gap.sim_put(2)
    fake_undulator_dcm.undulator.gap_motor.set = MagicMock()
    mock_load.return_value = np.array(
        [[5700, 5760, 6000, 6500, 7000], [5.4606, 5.5, 5.681, 6.045, 6.404]]
    )
    fake_undulator_dcm.dcm.energy_in_kev.user_readback.sim_put(14000)
    fake_undulator_dcm.energy.set()


# TODO: change this test
@patch("dodal.devices.undulator_dcm.loadtxt")
@patch("dodal.device.undulator_dcm.LOGGER")
def test_if_gap_is_wrong_then_logger_warning_and_gap_is_set(
    mock_load: MagicMock,
    mock_logger,
    fake_undulator: Undulator,
    fake_dcm: DCM,
    tmp_path,
):
    path = f"{tmp_path}/lookup.txt"

    fake_undulator.lookup_table_path = path
    create_energy_distance_table(path)
    fake_undulator.current_gap.sim_put(2)
    fake_undulator.gap_motor.set = MagicMock()
    fake_dcm.energy_in_kev.user_readback.sim_put(14000)

    assert verify_undulator_gap(fake_undulator, fake_dcm) is True
    mock_logger.warning.assert_called_once()
    fake_undulator.gap_motor.set.assert_called_once_with(5.674)


@patch("dodal.device.undulator_dcm.LOGGER")
def test_if_gap_is_correct_then_return_true_with_no_warnings(
    mock_logger, fake_undulator: Undulator, fake_dcm: DCM, tmp_path
):
    path = f"{tmp_path}/lookup.txt"
    fake_undulator.lookup_table_path = path
    create_energy_distance_table(path)
    fake_undulator.current_gap.sim_put(5.6815)
    fake_undulator.gap_motor.set = MagicMock()
    fake_dcm.energy_in_kev.user_readback.sim_put(6000)
    # assert verify_undulator_gap(fake_undulator, fake_dcm) is True
    mock_logger.warning.assert_not_called()
    fake_undulator.gap_motor.set.assert_not_called()
