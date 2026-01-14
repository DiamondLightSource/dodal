from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import (
    init_devices,
    set_mock_value,
)

from dodal.devices.insertion_device import (
    Apple2,
    Apple2Controller,
    Apple2LockedPhasesVal,
    Apple2Val,
    EnabledDisabledUpper,
    EnergyMotorConvertor,
    Pol,
    UndulatorGap,
    UndulatorGateStatus,
    UndulatorLockedPhaseAxes,
)

pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
async def mock_locked_apple2(
    mock_id_gap: UndulatorGap,
    mock_locked_phase_axes: UndulatorLockedPhaseAxes,
) -> Apple2:
    mock_locked_apple2 = Apple2(
        id_gap=mock_id_gap,
        id_phase=mock_locked_phase_axes,
    )
    return mock_locked_apple2


@pytest.fixture
async def mock_locked_phase_axes(
    prefix: str = "BLXX-EA-DET-007:",
) -> UndulatorLockedPhaseAxes:
    async with init_devices(mock=True):
        mock_phase_axes = UndulatorLockedPhaseAxes(
            prefix=prefix,
            top_outer="RPQ1",
            btm_inner="RPQ4",
        )
    assert mock_phase_axes.name == "mock_phase_axes"
    set_mock_value(mock_phase_axes.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_phase_axes.top_outer.velocity, 2)
    set_mock_value(mock_phase_axes.btm_inner.velocity, 2)
    set_mock_value(mock_phase_axes.top_outer.user_readback, 2)
    set_mock_value(mock_phase_axes.btm_inner.user_readback, 2)
    set_mock_value(mock_phase_axes.top_outer.user_setpoint_readback, 2)
    set_mock_value(mock_phase_axes.btm_inner.user_setpoint_readback, 2)
    set_mock_value(mock_phase_axes.status, EnabledDisabledUpper.ENABLED)
    return mock_phase_axes


class DummyLockedApple2Controller(Apple2Controller[Apple2[UndulatorLockedPhaseAxes]]):
    """Dummy class to test core logic of Apple2Controller."""

    def __init__(
        self,
        apple2: Apple2[UndulatorLockedPhaseAxes],
        gap_energy_motor_converter: EnergyMotorConvertor,
        phase_energy_motor_converter: EnergyMotorConvertor,
        name: str = "",
    ) -> None:
        super().__init__(
            apple2=apple2,
            gap_energy_motor_converter=gap_energy_motor_converter,
            phase_energy_motor_converter=phase_energy_motor_converter,
            name=name,
        )

    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        return Apple2Val(
            phase=Apple2LockedPhasesVal(top_outer=phase, btm_inner=phase),
            gap=gap,
        )


@pytest.fixture
def configured_gap() -> float:
    return 42.0


@pytest.fixture
def configured_phase() -> float:
    return 7.5


@pytest.fixture
async def mock_locked_controller(
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    configured_gap: float,
    configured_phase: float,
) -> DummyLockedApple2Controller:
    mock_locked_controller = DummyLockedApple2Controller(
        apple2=mock_locked_apple2,
        gap_energy_motor_converter=lambda energy, pol: configured_gap,
        phase_energy_motor_converter=lambda energy, pol: configured_phase,
    )
    return mock_locked_controller


@pytest.mark.parametrize(
    "pol, expect_top_outer, expect_btm_inner",
    [
        (Pol.LH, 0.0, 0.0),
        (Pol.LV, 24.0, 24.0),
        (Pol.PC, 16.5, 16.5),
        (Pol.NC, -15.5, -15.5),
        (Pol.LA, -16.4, 16.4),
        (Pol.LA, 16.4, -16.4),
    ],
)
async def test_id_polarisation_set_for_id_controller(
    mock_locked_controller: DummyLockedApple2Controller,
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    pol: Pol,
    expect_top_outer: float,
    expect_btm_inner: float,
):
    await mock_locked_controller.polarisation.set(pol)
    set_mock_value(mock_locked_apple2.phase().top_outer.user_readback, expect_top_outer)
    set_mock_value(mock_locked_apple2.phase().btm_inner.user_readback, expect_btm_inner)
    assert await mock_locked_controller.polarisation.get_value() == pol


async def test_id_controller_energy_sets_correct_values(
    mock_locked_controller: DummyLockedApple2Controller,
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    configured_gap: float,
    configured_phase: float,
):
    mock_locked_apple2.set = AsyncMock()
    mock_locked_controller._check_and_get_pol_setpoint = AsyncMock(return_value=Pol.LH)
    await mock_locked_controller.energy.set(100.0)
    expected_val = Apple2Val(
        phase=Apple2LockedPhasesVal(
            top_outer=configured_phase,
            btm_inner=configured_phase,
        ),
        gap=configured_gap,
    )
    mock_locked_apple2.set.assert_awaited_once_with(id_motor_values=expected_val)
