import asyncio
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from ophyd_async.core import (
    AsyncStatus,
    set_mock_value,
)

from dodal.devices.undulator import UndulatorGapAccess
from dodal.devices.undulator_dcm import (
    AccessError,
    UndulatorDCM,
    _get_closest_gap_for_energy,
)
from dodal.testing_utils import ID_GAP_LOOKUP_TABLE_PATH, MOCK_DAQ_CONFIG_PATH


def test_lookup_table_paths_passed(mock_undulator_dcm: UndulatorDCM):
    assert mock_undulator_dcm.id_gap_lookup_table_path == ID_GAP_LOOKUP_TABLE_PATH
    assert (
        mock_undulator_dcm.dcm_pitch_converter_lookup_table_path
        == MOCK_DAQ_CONFIG_PATH + "/lookup/BeamLineEnergy_DCM_Pitch_converter.txt"
    )
    assert (
        mock_undulator_dcm.dcm_roll_converter_lookup_table_path
        == MOCK_DAQ_CONFIG_PATH + "/lookup/BeamLineEnergy_DCM_Roll_converter.txt"
    )


async def test_fixed_offset_decoded(mock_undulator_dcm: UndulatorDCM):
    assert mock_undulator_dcm.dcm_fixed_offset_mm == 25.6


async def test_when_gap_access_is_disabled_set_energy_then_error_is_raised(
    mock_undulator_dcm: UndulatorDCM,
):
    set_mock_value(mock_undulator_dcm.undulator.gap_access, UndulatorGapAccess.DISABLED)
    with pytest.raises(AccessError):
        await mock_undulator_dcm.set(5)


@pytest.mark.parametrize(
    "dcm_energy, expected_output", [(5730, 5.4606), (7200, 6.045), (9000, 6.404)]
)
def test_correct_closest_distance_to_energy_from_table(dcm_energy, expected_output):
    energy_to_distance_table = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])
    assert (
        _get_closest_gap_for_energy(dcm_energy, energy_to_distance_table)
        == expected_output
    )


@patch("dodal.devices.util.lookup_tables.loadtxt")
@patch("dodal.devices.undulator_dcm.LOGGER")
async def test_if_gap_is_wrong_then_logger_info_is_called_and_gap_is_set_correctly(
    mock_logger: MagicMock, mock_load: MagicMock, mock_undulator_dcm: UndulatorDCM
):
    set_mock_value(mock_undulator_dcm.undulator.current_gap, 5.3)
    set_mock_value(mock_undulator_dcm.dcm.energy_in_kev.user_readback, 5.7)

    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])

    await mock_undulator_dcm.set(6.9)

    assert (await mock_undulator_dcm.dcm.energy_in_kev.user_setpoint.get_value()) == 6.9
    assert (
        await mock_undulator_dcm.undulator.gap_motor.user_setpoint.get_value()
    ) == 6.045
    mock_logger.info.assert_called()


@patch("dodal.devices.util.lookup_tables.loadtxt")
@patch("dodal.devices.undulator_dcm.LOGGER")
@patch("dodal.devices.undulator_dcm.TEST_MODE", True)
async def test_when_gap_access_is_not_checked_if_test_mode_enabled(
    mock_logger: MagicMock, mock_load: MagicMock, mock_undulator_dcm: UndulatorDCM
):
    set_mock_value(mock_undulator_dcm.undulator.gap_access, UndulatorGapAccess.DISABLED)
    set_mock_value(mock_undulator_dcm.undulator.current_gap, 5.3)
    set_mock_value(mock_undulator_dcm.dcm.energy_in_kev.user_readback, 5.7)

    set_mock_value(mock_undulator_dcm.undulator.gap_motor.user_setpoint, 0.0)
    set_mock_value(mock_undulator_dcm.undulator.gap_motor.user_readback, 0.0)

    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])

    await mock_undulator_dcm.set(6.9)

    assert (await mock_undulator_dcm.dcm.energy_in_kev.user_setpoint.get_value()) == 6.9
    # Verify undulator has not been asked to move
    assert (
        await mock_undulator_dcm.undulator.gap_motor.user_setpoint.get_value()
    ) == 0.0

    mock_logger.info.assert_called()
    mock_logger.debug.assert_called_once()


@patch("dodal.devices.util.lookup_tables.loadtxt")
@patch("dodal.devices.undulator_dcm.LOGGER")
async def test_if_gap_is_already_correct_then_dont_move_gap(
    mock_logger: MagicMock, mock_load: MagicMock, mock_undulator_dcm: UndulatorDCM
):
    set_mock_value(mock_undulator_dcm.dcm.energy_in_kev.user_setpoint, 0.0)
    set_mock_value(mock_undulator_dcm.dcm.energy_in_kev.user_readback, 0.0)

    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])
    set_mock_value(mock_undulator_dcm.undulator.current_gap, 5.4605)

    status = mock_undulator_dcm.set(5.8)
    await asyncio.wait_for(status, timeout=0.05)

    # Verify undulator has not been asked to move
    assert (
        await mock_undulator_dcm.undulator.gap_motor.user_setpoint.get_value()
    ) == 0.0
    mock_logger.info.assert_called_once()
    mock_logger.debug.assert_called_once()


async def test_energy_set_only_complete_when_all_statuses_are_finished(
    mock_undulator_dcm: UndulatorDCM,
):
    set_mock_value(mock_undulator_dcm.undulator.current_gap, 5.0)

    release_dcm = asyncio.Event()
    release_undulator = asyncio.Event()

    mock_undulator_dcm.dcm.energy_in_kev.set = MagicMock(
        return_value=AsyncStatus(release_dcm.wait())
    )
    mock_undulator_dcm.undulator.gap_motor.set = MagicMock(
        return_value=AsyncStatus(release_undulator.wait())
    )

    status = mock_undulator_dcm.set(5.0)

    assert not status.done
    release_dcm.set()
    assert not status.done
    release_undulator.set()
    await asyncio.wait_for(status, timeout=0.01)
