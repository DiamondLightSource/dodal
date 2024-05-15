import asyncio
from functools import partial
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from ophyd_async.core import (
    DirectoryInfo,
    DirectoryProvider,
    StaticDirectoryProvider,
    set_mock_value,
)
from ophyd_async.epics.motion import Motor


async def mock_good_coroutine():
    return asyncio.sleep(0)


def mock_move(motor: Motor, val, *args, **kwargs):
    set_mock_value(motor.user_setpoint, val)
    set_mock_value(motor.user_readback, val)
    return mock_good_coroutine()  # type: ignore


def patch_motor(motor: Motor, initial_position=0):
    set_mock_value(motor.user_setpoint, initial_position)
    set_mock_value(motor.user_readback, initial_position)
    set_mock_value(motor.deadband, 0.001)
    set_mock_value(motor.motor_done_move, 1)
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
