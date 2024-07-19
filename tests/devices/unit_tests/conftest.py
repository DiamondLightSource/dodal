from functools import partial
from pathlib import Path

import pytest
from ophyd_async.core import (
    DirectoryInfo,
    DirectoryProvider,
    StaticDirectoryProvider,
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)
from ophyd_async.epics.motion import Motor

from dodal.beamlines import i03
from dodal.common.beamlines.beamline_utils import clear_devices

DIRECTORY_INFO_FOR_TESTING: DirectoryInfo = DirectoryInfo(
    root=Path("/does/not/exist"),
    resource_dir=Path("/on/this/filesystem"),
)


def patch_motor(motor: Motor, initial_position=0):
    set_mock_value(motor.user_setpoint, initial_position)
    set_mock_value(motor.user_readback, initial_position)
    set_mock_value(motor.deadband, 0.001)
    set_mock_value(motor.motor_done_move, 1)
    set_mock_value(motor.velocity, 3)
    return callback_on_mock_put(
        motor.user_setpoint,
        lambda pos, *args, **kwargs: set_mock_value(motor.user_readback, pos),
    )


@pytest.fixture
def static_directory_provider(tmp_path: Path) -> DirectoryProvider:
    return StaticDirectoryProvider(tmp_path)


@pytest.fixture
def smargon():
    smargon = i03.smargon(fake_with_ophyd_sim=True)

    def mock_set(motor, value, *args, **kwargs):
        set_mock_value(motor.user_readback, value)

    def patch_motor(motor):
        get_mock_put(motor.user_setpoint).side_effect = partial(mock_set, motor)

    for motor in [smargon.omega, smargon.x, smargon.y, smargon.z]:
        patch_motor(motor)

    yield smargon

    clear_devices()
