import asyncio
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from ophyd_async.core import (
    AsyncStatus,
    DeviceCollector,
    set_sim_value,
)

from dodal.devices.dcm import DCM
from dodal.devices.undulator import Undulator, UndulatorGapAccess
from dodal.devices.undulator_dcm import (
    AccessError,
    UndulatorDCM,
    _get_closest_gap_for_energy,
    _get_energy_distance_table,
)

from ...conftest import MOCK_DAQ_CONFIG_PATH


@pytest.fixture
async def fake_undulator_dcm() -> UndulatorDCM:
    async with DeviceCollector(sim=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            lookup_table_path="./tests/devices/unit_tests/test_beamline_undulator_to_gap_lookup_table.txt",
        )
        dcm = DCM("DCM-01", name="dcm", daq_configuration_path=MOCK_DAQ_CONFIG_PATH)
        undulator_dcm = UndulatorDCM(undulator, dcm, name="undulator_dcm")
    return undulator_dcm


async def test_when_gap_access_is_disabled_set_energy_then_error_is_raised(
    fake_undulator_dcm: UndulatorDCM,
):
    set_sim_value(fake_undulator_dcm.undulator.gap_access, UndulatorGapAccess.DISABLED)
    with pytest.raises(AccessError):
        await fake_undulator_dcm.set(5)


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
async def test_if_gap_is_wrong_then_logger_info_is_called_and_gap_is_set_correctly(
    mock_logger: MagicMock, mock_load: MagicMock, fake_undulator_dcm: UndulatorDCM
):
    set_sim_value(fake_undulator_dcm.undulator.current_gap, 5.3)
    set_sim_value(fake_undulator_dcm.dcm.energy_in_kev.readback, 5.7)

    # fake_undulator_dcm.undulator.gap_motor.move = MagicMock()
    # fake_undulator_dcm.dcm.energy_in_kev.move = MagicMock()
    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])

    await fake_undulator_dcm.set(6.9)

    assert (await fake_undulator_dcm.dcm.energy_in_kev.setpoint.get_value()) == 6.9
    assert (await fake_undulator_dcm.undulator.gap_motor.setpoint.get_value()) == 6.045
    mock_logger.info.assert_called()


@patch("dodal.devices.undulator_dcm.loadtxt")
@patch("dodal.devices.undulator_dcm.LOGGER")
@patch("dodal.devices.undulator_dcm.TEST_MODE", True)
async def test_when_gap_access_is_not_checked_if_test_mode_enabled(
    mock_logger: MagicMock, mock_load: MagicMock, fake_undulator_dcm: UndulatorDCM
):
    set_sim_value(fake_undulator_dcm.undulator.gap_access, UndulatorGapAccess.DISABLED)
    set_sim_value(fake_undulator_dcm.undulator.current_gap, 5.3)
    set_sim_value(fake_undulator_dcm.dcm.energy_in_kev.readback, 5.7)

    set_sim_value(fake_undulator_dcm.undulator.gap_motor.setpoint, 0.0)
    set_sim_value(fake_undulator_dcm.undulator.gap_motor.readback, 0.0)

    # fake_undulator_dcm.undulator.gap_motor.move = MagicMock()
    # fake_undulator_dcm.dcm.energy_in_kev.move = MagicMock()
    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])

    await fake_undulator_dcm.set(6.9)

    assert (await fake_undulator_dcm.dcm.energy_in_kev.setpoint.get_value()) == 6.9
    # Verify undulator has not been asked to move
    assert (await fake_undulator_dcm.undulator.gap_motor.setpoint.get_value()) == 0.0

    mock_logger.info.assert_called()


@patch("dodal.devices.undulator_dcm.loadtxt")
@patch("dodal.devices.undulator_dcm.LOGGER")
async def test_if_gap_is_already_correct_then_dont_move_gap(
    mock_logger: MagicMock, mock_load: MagicMock, fake_undulator_dcm: UndulatorDCM
):
    set_sim_value(fake_undulator_dcm.dcm.energy_in_kev.setpoint, 0.0)
    set_sim_value(fake_undulator_dcm.dcm.energy_in_kev.readback, 0.0)
    # fake_undulator_dcm.undulator.gap_motor.move = MagicMock()
    # fake_undulator_dcm.dcm.energy_in_kev.move = MagicMock()
    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])
    set_sim_value(fake_undulator_dcm.undulator.current_gap, 5.4605)

    status = fake_undulator_dcm.set(5.8)
    await asyncio.wait_for(status, timeout=0.01)

    # Verify undulator has not been asked to move
    assert (await fake_undulator_dcm.undulator.gap_motor.setpoint.get_value()) == 0.0
    mock_logger.info.assert_called_once()


async def test_energy_set_only_complete_when_all_statuses_are_finished(
    fake_undulator_dcm: UndulatorDCM,
):
    set_sim_value(fake_undulator_dcm.undulator.current_gap, 5.0)

    release_dcm = asyncio.Event()
    release_undulator = asyncio.Event()

    fake_undulator_dcm.dcm.energy_in_kev.set = MagicMock(
        return_value=AsyncStatus(release_dcm.wait())
    )
    fake_undulator_dcm.undulator.gap_motor.set = MagicMock(
        return_value=AsyncStatus(release_undulator.wait())
    )

    status = fake_undulator_dcm.set(5.0)

    assert not status.done
    release_dcm.set()
    assert not status.done
    release_undulator.set()
    await asyncio.wait_for(status, timeout=0.01)
