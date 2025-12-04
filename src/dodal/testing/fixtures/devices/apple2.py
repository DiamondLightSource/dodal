from unittest.mock import MagicMock

import pytest
from daq_config_server.client import ConfigServer
from ophyd_async.core import (
    init_devices,
    set_mock_value,
)

from dodal.devices.insertion_device.apple2_undulator import (
    EnabledDisabledUpper,
    UndulatorGap,
    UndulatorGateStatus,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)


@pytest.fixture
def mock_config_client() -> ConfigServer:
    mock_config_client = ConfigServer()

    mock_config_client.get_file_contents = MagicMock(spec=["get_file_contents"])

    def my_side_effect(file_path, reset_cached_result) -> str:
        assert reset_cached_result is True
        with open(file_path) as f:
            return f.read()

    mock_config_client.get_file_contents.side_effect = my_side_effect
    return mock_config_client


@pytest.fixture
async def mock_id_gap(prefix: str = "BLXX-EA-DET-007:") -> UndulatorGap:
    async with init_devices(mock=True):
        mock_id_gap = UndulatorGap(prefix, "mock_id_gap")
    assert mock_id_gap.name == "mock_id_gap"
    set_mock_value(mock_id_gap.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_id_gap.velocity, 1)
    set_mock_value(mock_id_gap.user_readback, 1)
    set_mock_value(mock_id_gap.user_setpoint, "1")
    set_mock_value(mock_id_gap.status, EnabledDisabledUpper.ENABLED)
    return mock_id_gap


@pytest.fixture
async def mock_phase_axes(prefix: str = "BLXX-EA-DET-007:") -> UndulatorPhaseAxes:
    async with init_devices(mock=True):
        mock_phase_axes = UndulatorPhaseAxes(
            prefix=prefix,
            top_outer="RPQ1",
            top_inner="RPQ2",
            btm_outer="RPQ3",
            btm_inner="RPQ4",
        )
    assert mock_phase_axes.name == "mock_phase_axes"
    set_mock_value(mock_phase_axes.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_phase_axes.top_outer.velocity, 2)
    set_mock_value(mock_phase_axes.top_inner.velocity, 2)
    set_mock_value(mock_phase_axes.btm_outer.velocity, 2)
    set_mock_value(mock_phase_axes.btm_inner.velocity, 2)
    set_mock_value(mock_phase_axes.status, EnabledDisabledUpper.ENABLED)
    return mock_phase_axes


@pytest.fixture
async def mock_jaw_phase(prefix: str = "BLXX-EA-DET-007:") -> UndulatorJawPhase:
    async with init_devices(mock=True):
        mock_jaw_phase = UndulatorJawPhase(
            prefix=prefix, move_pv="RPQ1", jaw_phase="JAW"
        )
    set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_jaw_phase.jaw_phase.velocity, 2)
    set_mock_value(mock_jaw_phase.jaw_phase.user_readback, 0)
    set_mock_value(mock_jaw_phase.jaw_phase.user_setpoint_readback, 0)
    set_mock_value(mock_jaw_phase.status, EnabledDisabledUpper.ENABLED)
    return mock_jaw_phase
