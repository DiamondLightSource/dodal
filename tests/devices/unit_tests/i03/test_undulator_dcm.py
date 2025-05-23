import asyncio
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from ophyd_async.core import AsyncStatus, init_devices
from ophyd_async.testing import get_mock_put, set_mock_value

from conftest import MOCK_DAQ_CONFIG_PATH
from dodal.devices.i03.dcm import DCM
from dodal.devices.i03.undulator_dcm import UndulatorDCM
from dodal.devices.undulator import AccessError, Undulator, UndulatorGapAccess
from dodal.devices.util.test_utils import patch_motor
from dodal.log import LOGGER
from tests.constants import UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH


@pytest.fixture(autouse=True)
def flush_event_loop_on_finish(event_loop):
    # wait for the test function to complete
    yield None

    if pending_tasks := asyncio.all_tasks(event_loop):
        LOGGER.warning(f"Waiting for pending tasks to complete {pending_tasks}")
        event_loop.run_until_complete(asyncio.gather(*pending_tasks))


@pytest.fixture
async def fake_undulator_dcm(RE) -> UndulatorDCM:
    async with init_devices(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            poles=80,
            id_gap_lookup_table_path=UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH,
            length=2.0,
        )
        dcm = DCM("DCM-01", name="dcm")
        undulator_dcm = UndulatorDCM(
            undulator,
            dcm,
            daq_configuration_path=MOCK_DAQ_CONFIG_PATH,
            name="undulator_dcm",
        )
    patch_motor(dcm.offset_in_mm)
    return undulator_dcm


def test_lookup_table_paths_passed(fake_undulator_dcm: UndulatorDCM):
    assert (
        fake_undulator_dcm.undulator_ref().id_gap_lookup_table_path
        == UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH
    )
    assert (
        fake_undulator_dcm.pitch_energy_table_path
        == MOCK_DAQ_CONFIG_PATH + "/lookup/BeamLineEnergy_DCM_Pitch_converter.txt"
    )
    assert (
        fake_undulator_dcm.roll_energy_table_path
        == MOCK_DAQ_CONFIG_PATH + "/lookup/BeamLineEnergy_DCM_Roll_converter.txt"
    )


async def test_fixed_offset_decoded(fake_undulator_dcm: UndulatorDCM):
    assert fake_undulator_dcm.dcm_fixed_offset_mm == 25.6


@patch("dodal.devices.util.lookup_tables.loadtxt")
@patch("dodal.devices.undulator.LOGGER")
async def test_if_gap_is_wrong_then_logger_info_is_called_and_gap_is_set_correctly(
    mock_logger: MagicMock, mock_load: MagicMock, fake_undulator_dcm: UndulatorDCM
):
    set_mock_value(fake_undulator_dcm.undulator_ref().current_gap, 5.3)
    set_mock_value(fake_undulator_dcm.dcm_ref().energy_in_kev.user_readback, 5.7)

    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])

    await fake_undulator_dcm.set(6.9)

    assert (
        await fake_undulator_dcm.dcm_ref().energy_in_kev.user_setpoint.get_value()
    ) == 6.9
    assert (
        await fake_undulator_dcm.undulator_ref().gap_motor.user_setpoint.get_value()
    ) == 6.000046153846154
    assert (
        await fake_undulator_dcm.dcm_ref().offset_in_mm.user_setpoint.get_value()
    ) == 25.6
    mock_logger.info.assert_called()


@patch("dodal.devices.util.lookup_tables.loadtxt")
@patch("dodal.devices.undulator.LOGGER")
@patch("dodal.devices.undulator.TEST_MODE", True)
async def test_when_gap_access_is_not_checked_if_test_mode_enabled(
    mock_logger: MagicMock, mock_load: MagicMock, fake_undulator_dcm: UndulatorDCM
):
    set_mock_value(
        fake_undulator_dcm.undulator_ref().gap_access, UndulatorGapAccess.DISABLED
    )
    set_mock_value(fake_undulator_dcm.undulator_ref().current_gap, 5.3)
    set_mock_value(fake_undulator_dcm.dcm_ref().energy_in_kev.user_readback, 5.7)

    set_mock_value(fake_undulator_dcm.undulator_ref().gap_motor.user_setpoint, 0.0)
    set_mock_value(fake_undulator_dcm.undulator_ref().gap_motor.user_readback, 0.0)

    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])

    await fake_undulator_dcm.set(6.9)

    assert (
        await fake_undulator_dcm.dcm_ref().energy_in_kev.user_setpoint.get_value()
    ) == 6.9
    # Verify undulator has not been asked to move
    assert (
        await fake_undulator_dcm.undulator_ref().gap_motor.user_setpoint.get_value()
    ) == 0.0

    mock_logger.info.assert_called()
    mock_logger.debug.assert_called_once()


@patch("dodal.devices.util.lookup_tables.loadtxt")
@patch("dodal.devices.undulator.LOGGER")
async def test_if_gap_is_already_correct_then_dont_move_gap(
    mock_logger: MagicMock, mock_load: MagicMock, fake_undulator_dcm: UndulatorDCM
):
    set_mock_value(fake_undulator_dcm.dcm_ref().energy_in_kev.user_setpoint, 0.0)
    set_mock_value(fake_undulator_dcm.dcm_ref().energy_in_kev.user_readback, 0.0)

    mock_load.return_value = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])
    set_mock_value(fake_undulator_dcm.undulator_ref().current_gap, 5.4605)

    await fake_undulator_dcm.set(5.7001)

    # Verify undulator has not been asked to move
    assert (
        await fake_undulator_dcm.undulator_ref().gap_motor.user_setpoint.get_value()
    ) == 0.0
    mock_logger.info.assert_called_once()
    mock_logger.debug.assert_called_once()


async def test_dcm_offset_only_set_when_energy_set_completes(
    fake_undulator_dcm: UndulatorDCM,
):
    set_mock_value(fake_undulator_dcm.undulator_ref().current_gap, 5.0)

    release_dcm = asyncio.Event()
    release_undulator = asyncio.Event()

    fake_undulator_dcm.dcm_ref().energy_in_kev.set = MagicMock(
        return_value=AsyncStatus(release_dcm.wait())
    )
    fake_undulator_dcm.undulator_ref().gap_motor.set = MagicMock(
        return_value=AsyncStatus(release_undulator.wait())
    )

    offset_put = get_mock_put(fake_undulator_dcm.dcm_ref().offset_in_mm.user_setpoint)
    status = fake_undulator_dcm.set(5.0)

    await asyncio.wait([status.task], timeout=0.1)  # type: ignore
    offset_put.assert_not_called()
    release_dcm.set()
    await asyncio.wait([status.task], timeout=0.1)  # type: ignore
    offset_put.assert_not_called()
    release_undulator.set()
    await asyncio.wait_for(status, timeout=1)
    offset_put.assert_called_with(25.6, wait=True)


async def test_energy_set_only_complete_when_all_statuses_are_finished(
    fake_undulator_dcm: UndulatorDCM,
):
    set_mock_value(fake_undulator_dcm.undulator_ref().current_gap, 5.0)

    release_dcm = asyncio.Event()
    release_undulator = asyncio.Event()

    fake_undulator_dcm.dcm_ref().energy_in_kev.set = MagicMock(
        return_value=AsyncStatus(release_dcm.wait())
    )
    fake_undulator_dcm.undulator_ref().gap_motor.set = MagicMock(
        return_value=AsyncStatus(release_undulator.wait())
    )

    status = fake_undulator_dcm.set(5.0)

    await asyncio.wait([status.task], timeout=0.1)  # type: ignore
    assert not status.done
    release_dcm.set()
    await asyncio.wait([status.task], timeout=0.1)  # type: ignore
    assert not status.done
    release_undulator.set()
    await asyncio.wait_for(status, timeout=0.02)


async def test_when_undulator_gap_is_disabled_setting_energy_errors_and_dcm_energy_is_not_set(
    fake_undulator_dcm: UndulatorDCM,
):
    set_mock_value(
        fake_undulator_dcm.undulator_ref().gap_access, UndulatorGapAccess.DISABLED
    )

    with pytest.raises(AccessError):
        await fake_undulator_dcm.set(5)

    get_mock_put(
        fake_undulator_dcm.dcm_ref().energy_in_kev.user_setpoint
    ).assert_not_called()
