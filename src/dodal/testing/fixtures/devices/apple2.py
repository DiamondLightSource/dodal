import pytest
from ophyd_async.core import init_devices, set_mock_value

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.insertion_device import (
    Apple2,
    UndulatorAccessControl,
    UndulatorGap,
    UndulatorGateStatus,
    UndulatorJawPhase,
    UndulatorLockedPhaseAxes,
    UndulatorPhaseAxes,
)

PREFIX = "BLXX-EA-DET-007:"


@pytest.fixture
def mock_id_access_control() -> UndulatorAccessControl:
    with init_devices(mock=True):
        mock_id_access_control = UndulatorAccessControl(PREFIX)

    set_mock_value(mock_id_access_control.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_id_access_control.status, EnabledDisabledUpper.ENABLED)
    return mock_id_access_control


@pytest.fixture
async def mock_id_gap(mock_id_access_control: UndulatorAccessControl) -> UndulatorGap:
    async with init_devices(mock=True):
        mock_id_gap = UndulatorGap(PREFIX, mock_id_access_control)
    set_mock_value(mock_id_gap.velocity, 1)
    set_mock_value(mock_id_gap.user_readback, 1)
    set_mock_value(mock_id_gap.user_setpoint_str, "1")
    return mock_id_gap


@pytest.fixture
async def mock_phase_axes(
    mock_id_access_control: UndulatorAccessControl,
) -> UndulatorPhaseAxes:
    async with init_devices(mock=True):
        mock_phase_axes = UndulatorPhaseAxes(
            prefix=PREFIX,
            top_outer="RPQ1",
            top_inner="RPQ2",
            btm_outer="RPQ3",
            btm_inner="RPQ4",
            access_control=mock_id_access_control,
        )
    assert mock_phase_axes.name == "mock_phase_axes"
    set_mock_value(mock_phase_axes.top_outer.velocity, 2)
    set_mock_value(mock_phase_axes.top_inner.velocity, 2)
    set_mock_value(mock_phase_axes.btm_outer.velocity, 2)
    set_mock_value(mock_phase_axes.btm_inner.velocity, 2)
    return mock_phase_axes


@pytest.fixture
async def mock_jaw_phase(
    mock_id_access_control: UndulatorAccessControl,
) -> UndulatorJawPhase:
    async with init_devices(mock=True):
        mock_jaw_phase = UndulatorJawPhase(
            prefix=PREFIX,
            move_pv="RPQ1",
            jaw_phase="JAW",
            access_control=mock_id_access_control,
        )
    set_mock_value(mock_jaw_phase.jaw_phase.velocity, 2)
    set_mock_value(mock_jaw_phase.jaw_phase.user_readback, 0)
    set_mock_value(mock_jaw_phase.jaw_phase.user_setpoint_readback, 0)
    return mock_jaw_phase


@pytest.fixture
async def mock_locked_phase_axes(
    mock_id_access_control: UndulatorAccessControl,
) -> UndulatorLockedPhaseAxes:
    async with init_devices(mock=True):
        mock_phase_axes = UndulatorLockedPhaseAxes(
            prefix=PREFIX,
            top_outer="RPQ1",
            btm_inner="RPQ4",
            access_control=mock_id_access_control,
        )
    assert mock_phase_axes.name == "mock_phase_axes"
    set_mock_value(mock_phase_axes.top_outer.velocity, 2)
    set_mock_value(mock_phase_axes.btm_inner.velocity, 2)
    set_mock_value(mock_phase_axes.top_outer.user_readback, 2)
    set_mock_value(mock_phase_axes.btm_inner.user_readback, 2)
    set_mock_value(mock_phase_axes.top_outer.user_setpoint_readback, 2)
    set_mock_value(mock_phase_axes.btm_inner.user_setpoint_readback, 2)
    return mock_phase_axes


@pytest.fixture
async def mock_locked_apple2(
    mock_id_gap: UndulatorGap,
    mock_locked_phase_axes: UndulatorLockedPhaseAxes,
    mock_id_access_control: UndulatorAccessControl,
) -> Apple2[UndulatorLockedPhaseAxes]:
    with init_devices(mock=True):
        mock_locked_apple2 = Apple2[UndulatorLockedPhaseAxes](
            gap=mock_id_gap,
            phase=mock_locked_phase_axes,
            access_control=mock_id_access_control,
        )
    return mock_locked_apple2
