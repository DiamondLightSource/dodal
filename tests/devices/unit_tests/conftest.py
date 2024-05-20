from pathlib import Path
from unittest.mock import MagicMock

import pytest
from ophyd_async.core import (
    DirectoryInfo,
    DirectoryProvider,
    StaticDirectoryProvider,
    callback_on_mock_put,
    set_mock_value,
)
from ophyd_async.epics.motion import Motor

DIRECTORY_INFO_FOR_TESTING: DirectoryInfo = DirectoryInfo(
    root=Path("/does/not/exist"),
    resource_dir=Path("/on/this/filesystem"),
)


def pass_on_mock(motor, call_log: MagicMock | None = None):
    def _pass_on_mock(value, **kwargs):
        set_mock_value(motor.user_readback, value)
        if call_log is not None:
            call_log(value, **kwargs)

    return _pass_on_mock


def patch_motor(motor: Motor, initial_position=0, call_log: MagicMock | None = None):
    set_mock_value(motor.user_setpoint, initial_position)
    set_mock_value(motor.user_readback, initial_position)
    set_mock_value(motor.deadband, 0.001)
    set_mock_value(motor.motor_done_move, 1)
    return callback_on_mock_put(motor.user_setpoint, pass_on_mock(motor, call_log))


@pytest.fixture
def static_directory_provider(tmp_path: Path) -> DirectoryProvider:
    return StaticDirectoryProvider(tmp_path)
