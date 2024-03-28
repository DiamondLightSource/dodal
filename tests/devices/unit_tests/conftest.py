from functools import partial
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from ophyd.epics_motor import EpicsMotor
from ophyd.status import Status
from ophyd_async.core import DirectoryInfo, DirectoryProvider, StaticDirectoryProvider

from dodal.devices.util.motor_utils import ExtendedEpicsMotor


def mock_set(motor: EpicsMotor, val):
    motor.user_setpoint.sim_put(val)  # type: ignore
    motor.user_readback.sim_put(val)  # type: ignore
    return Status(done=True, success=True)


def patch_motor(motor: EpicsMotor | ExtendedEpicsMotor, initial_position=0):
    motor.user_setpoint.sim_put(initial_position)  # type: ignore
    motor.user_readback.sim_put(initial_position)  # type: ignore
    motor.motor_done_move.sim_put(1)  # type: ignore
    motor.user_setpoint._use_limits = False
    if isinstance(motor, ExtendedEpicsMotor):
        motor.motor_resolution.sim_put(0.001)  # type: ignore
    return patch.object(motor, "set", MagicMock(side_effect=partial(mock_set, motor)))


DIRECTORY_INFO_FOR_TESTING: DirectoryInfo = DirectoryInfo(
    root=Path("/does/not/exist"),
    resource_dir=Path("/on/this/filesystem"),
)


@pytest.fixture
def static_directory_provider(tmp_path: Path) -> DirectoryProvider:
    return StaticDirectoryProvider(tmp_path)
