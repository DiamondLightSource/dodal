from unittest.mock import patch

from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    set_mock_value,
)

import dodal.plan_stubs.pressure_jump_cell as pressure_cell_stubs
from dodal.devices.pressure_jump_cell import (
    PressureJumpCell,
    PressureJumpCellController,
    PressureJumpParameters,
)


def test_set_pressure_stub_calls_control_set(
    run_engine: RunEngine, cell_with_mocked_busy: PressureJumpCell
):
    target_pressure = 1234
    set_mock_value(cell_with_mocked_busy.control.timeout, 1)

    with patch.object(
        PressureJumpCellController,
        "set",
        side_effect=PressureJumpCellController.set,
        autospec=True,
    ) as fake_control_set:
        run_engine(
            pressure_cell_stubs.set_pressure(cell_with_mocked_busy, target_pressure)
        )

    # Functionality of control.set checked in device tests so just check plan stub calls set
    fake_control_set.assert_called_once_with(
        cell_with_mocked_busy.control, target_pressure
    )


def test_set_pressure_jump_stub_calls_control_set(
    run_engine: RunEngine, cell_with_mocked_busy: PressureJumpCell
):
    target_jump = PressureJumpParameters(123, 5678)

    set_mock_value(cell_with_mocked_busy.control.timeout, 1)

    with patch.object(
        PressureJumpCellController,
        "set",
        side_effect=PressureJumpCellController.set,
        autospec=True,
    ) as fake_control_set:
        run_engine(
            pressure_cell_stubs.set_pressure_jump(
                cell_with_mocked_busy,
                target_jump.pressure_from,
                target_jump.pressure_to,
            )
        )
    # Functionality of control.set checked in device tests so just check plan stub calls set
    fake_control_set.assert_called_once_with(cell_with_mocked_busy.control, target_jump)
