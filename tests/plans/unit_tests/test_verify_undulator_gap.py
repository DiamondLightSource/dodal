from unittest.mock import MagicMock, patch

import pytest
from ophyd.sim import make_fake_device

from dodal.devices.DCM import DCM
from dodal.devices.undulator import Undulator
from dodal.plans.verify_undulator_gap import (
    UndulatorGapAccess,
    _get_closest_gap_to_dcm_energy,
    _get_energy_to_distance_table,
    verify_undulator_gap,
)


@pytest.fixture
def fake_undulator() -> Undulator:
    undulator = make_fake_device(Undulator)(name="undulator")
    return undulator


@pytest.fixture
def fake_dcm() -> DCM:
    dcm = make_fake_device(DCM)(name="dcm")
    return dcm


@patch("dodal.plans.verify_undulator_gap.LOGGER")
def test_when_gap_access_is_disabled_function_returns_false_and_logger_gives_warning(
    mock_logger, fake_dcm: DCM, fake_undulator: Undulator
):
    fake_undulator.gap_access.sim_put(UndulatorGapAccess.DISABLED.value)
    assert (
        verify_undulator_gap(fake_undulator, fake_dcm, fake_undulator.lookup_table_path)
        is False
    )
    mock_logger.warning.assert_called_once()


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


def test_energy_to_distance_table_correct_format(fake_undulator: Undulator, tmp_path):
    path = f"{tmp_path}/lookup.txt"
    create_energy_distance_table(path)
    table = _get_energy_to_distance_table(path)
    assert table[5700] == 5.4606
    assert table[14000] == 5.674
    assert table[6000] == 5.681


@pytest.mark.parametrize(
    "dcm_energy, expected_output", [(5730, 5.4606), (6505, 6.045), (7010, 6.404)]
)
def test_correct_closest_distance_to_energy_from_table(
    dcm_energy, expected_output, fake_undulator: Undulator, fake_dcm: DCM
):
    energy_to_distance_table = {
        5700: 5.4606,
        5760: 5.5,
        6000: 5.681,
        6500: 6.045,
        7000: 6.404,
    }
    assert (
        _get_closest_gap_to_dcm_energy(dcm_energy, energy_to_distance_table)
        == expected_output
    )


@patch("dodal.plans.verify_undulator_gap.LOGGER")
def test_if_gap_is_wrong_then_logger_warning_and_gap_is_set(
    mock_logger, fake_undulator: Undulator, fake_dcm: DCM, tmp_path
):
    path = f"{tmp_path}/lookup.txt"

    fake_undulator.lookup_table_path = path
    create_energy_distance_table(path)
    fake_undulator.gap.user_readback.sim_put(2)
    fake_undulator.gap.set = MagicMock()
    fake_dcm.energy_in_kev.user_readback.sim_put(14000)

    assert verify_undulator_gap(fake_undulator, fake_dcm) is True
    mock_logger.warning.assert_called_once()
    fake_undulator.gap.set.assert_called_once_with(5.674)


@patch("dodal.plans.verify_undulator_gap.LOGGER")
def test_if_gap_is_correct_then_return_true_with_no_warnings(
    mock_logger, fake_undulator: Undulator, fake_dcm: DCM, tmp_path
):
    path = f"{tmp_path}/lookup.txt"
    fake_undulator.lookup_table_path = path
    create_energy_distance_table(path)
    fake_undulator.gap.user_readback.sim_put(5.6815)
    fake_undulator.gap.set = MagicMock()
    fake_dcm.energy_in_kev.user_readback.sim_put(6000)
    assert verify_undulator_gap(fake_undulator, fake_dcm) is True
    mock_logger.warning.assert_not_called()
    fake_undulator.gap.set.assert_not_called()
