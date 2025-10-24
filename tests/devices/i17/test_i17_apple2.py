from unittest.mock import AsyncMock, MagicMock

import pytest
from ophyd_async.core import init_devices

from dodal.devices.apple2_undulator import (
    Apple2,
    Apple2Val,
    Pol,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.i17.i17_apple2 import I17Apple2Controller


@pytest.fixture
async def mock_apple2():
    async with init_devices(mock=True):
        mock_id_gap = UndulatorGap("BLXX-EA-DET-007:")
        mock_phase_axes = UndulatorPhaseAxes(
            "BLXX-EA-DET-007:",
            top_outer="RPQ1",
            top_inner="RPQ2",
            btm_outer="RPQ3",
            btm_inner="RPQ4",
        )
    mock_apple2 = Apple2(id_gap=mock_id_gap, id_phase=mock_phase_axes)

    return mock_apple2


async def test_set_motors_from_energy_sets_correct_values(mock_apple2: Apple2):
    mock_apple2.set = AsyncMock()
    mock_energy_to_motor = MagicMock(return_value=(42.0, 7.5))
    controller = I17Apple2Controller(
        apple2=mock_apple2,
        energy_to_motor_converter=mock_energy_to_motor,
        name="test_id",
    )
    # Mock polarisation setpoint check
    controller._check_and_get_pol_setpoint = AsyncMock(return_value=Pol.LH)
    await controller._set_motors_from_energy(100.0)
    mock_energy_to_motor.assert_called_once_with(energy=100.0, pol=Pol.LH)
    expected_val = Apple2Val(
        top_outer=f"{7.5:.6f}",
        top_inner="0.0",
        btm_inner=f"{7.5:.6f}",
        btm_outer="0.0",
        gap=f"{42.0:.6f}",
    )
    mock_apple2.set.assert_awaited_once_with(id_motor_values=expected_val)
