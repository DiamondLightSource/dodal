import asyncio
from functools import partial
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from ophyd_async.core import DirectoryInfo, DirectoryProvider, StaticDirectoryProvider
from ophyd_async.epics.motion import Motor


async def mock_good_coroutine():
    return asyncio.sleep(0)


def mock_move(motor: Motor, val, *args, **kwargs):
    motor.user_setpoint._backend._set_value(val)  # type: ignore
    motor.user_readback._backend._set_value(val)  # type: ignore
    return mock_good_coroutine()  # type: ignore


def patch_motor(motor: Motor, initial_position=0):
    motor.user_setpoint._backend._set_value(initial_position)  # type: ignore
    motor.user_readback._backend._set_value(initial_position)  # type: ignore
    motor.deadband._backend._set_value(0.001)  # type: ignore
    motor.motor_done_move._backend._set_value(1)  # type: ignore
    return patch.object(
        motor, "_move", AsyncMock(side_effect=partial(mock_move, motor))
    )


DIRECTORY_INFO_FOR_TESTING: DirectoryInfo = DirectoryInfo(
    root=Path("/does/not/exist"),
    resource_dir=Path("/on/this/filesystem"),
)


@pytest.fixture
def static_directory_provider(tmp_path: Path) -> DirectoryProvider:
    return StaticDirectoryProvider(tmp_path)
