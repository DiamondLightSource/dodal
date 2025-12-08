from unittest.mock import AsyncMock, MagicMock

import pytest
from ophyd_async.core import init_devices

from dodal.devices.i17.i17_apple2 import I17Apple2Controller
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    Apple2PhasesVal,
    Apple2Val,
    Pol,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import EnergyMotorLookup

# add mock_config_client, mock_id_gap, mock_phase and mock_jaw_phase_axes to pytest.
pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
async def mock_apple2(
    mock_id_gap: UndulatorGap, mock_phase_axes: UndulatorPhaseAxes
) -> Apple2:
    async with init_devices(mock=True):
        mock_apple2 = Apple2(id_gap=mock_id_gap, id_phase=mock_phase_axes)
    return mock_apple2


@pytest.fixture
async def mock_id_controller(
    mock_apple2: Apple2[UndulatorPhaseAxes],
) -> I17Apple2Controller:
    mock_gap_energy_motor_lut = EnergyMotorLookup()
    mock_gap_energy_motor_lut.find_value_in_lookup_table = MagicMock(return_value=42.0)
    mock_phase_energy_motor_lut = EnergyMotorLookup()
    mock_phase_energy_motor_lut.find_value_in_lookup_table = MagicMock(return_value=7.5)
    with init_devices(mock=True):
        mock_id_controller = I17Apple2Controller(
            apple2=mock_apple2,
            gap_energy_motor_lut=mock_gap_energy_motor_lut,
            phase_energy_motor_lut=mock_phase_energy_motor_lut,
        )
    return mock_id_controller


async def test_set_motors_from_energy_and_polarisation_sets_correct_values(
    mock_id_controller: I17Apple2Controller,
    mock_apple2: Apple2[UndulatorPhaseAxes],
):
    mock_apple2.set = AsyncMock()
    # Mock polarisation setpoint check
    mock_id_controller._check_and_get_pol_setpoint = AsyncMock(return_value=Pol.LH)
    await mock_id_controller.energy.set(100.0)
    mock_id_controller.gap_energy_motor_converter.assert_called_once_with(  # type:ignore
        energy=100.0, pol=Pol.LH
    )
    mock_id_controller.phase_energy_motor_converter.assert_called_once_with(  # type:ignore
        energy=100.0, pol=Pol.LH
    )
    expected_val = Apple2Val(
        gap=f"{42.0:.6f}",
        phase=Apple2PhasesVal(
            top_outer=f"{7.5:.6f}",
            top_inner=f"{0.0:.6f}",
            btm_inner=f"{7.5:.6f}",
            btm_outer=f"{0.0:.6f}",
        ),
    )
    mock_apple2.set.assert_awaited_once_with(id_motor_values=expected_val)
