from unittest.mock import patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    init_devices,
    set_mock_value,
)

import dodal.plan_stubs.pressure_jump_cell as pressure_cell_stubs
from dodal.devices.pressure_jump_cell import (
    DoJump,
    PressureJumpCell,
)


@pytest.fixture
async def cell() -> PressureJumpCell:
    async with init_devices(mock=True):
        pjump = PressureJumpCell("DEMO-PJUMPCELL-01:")

    return pjump


def test_set_pressure_jump_stub_calls_control_set(
    run_engine: RunEngine, cell: PressureJumpCell
):
    target_pressure_from = 123
    target_pressure_to = 5678

    set_mock_value(cell.control.timeout, 1)

    with patch.object(
        DoJump,
        "trigger",
        side_effect=DoJump.trigger,
        autospec=True,
    ) as fake_dojump_trigger:
        run_engine(
            pressure_cell_stubs.set_pressure_jump(
                cell, target_pressure_from, target_pressure_to
            )
        )

    # Functionality of control.set checked in device tests so just check plan stub calls trigger
    fake_dojump_trigger.assert_called_once()
