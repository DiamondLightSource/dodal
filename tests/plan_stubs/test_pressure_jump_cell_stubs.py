from unittest.mock import patch

from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    set_mock_value,
)

import dodal.plan_stubs.pressure_jump_cell as pressure_cell_stubs
from dodal.devices.pressure_jump_cell import (
    DoJump,
    PressureJumpCell,
)


def test_set_pressure_jump_stub_calls_control_set(
    run_engine: RunEngine, cell_with_mocked_busy: PressureJumpCell
):
    target_pressure_from = 123
    target_pressure_to = 5678

    set_mock_value(cell_with_mocked_busy.control.timeout, 1)

    with patch.object(
        DoJump,
        "trigger",
        side_effect=DoJump.trigger,
        autospec=True,
    ) as fake_dojump_trigger:
        run_engine(
            pressure_cell_stubs.set_pressure_jump(
                cell_with_mocked_busy, target_pressure_from, target_pressure_to
            )
        )

    # Functionality of control.set checked in device tests so just check plan stub calls trigger
    fake_dojump_trigger.assert_called_once()
