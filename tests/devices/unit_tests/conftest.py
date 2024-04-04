import asyncio
from functools import partial
from typing import Union
from unittest.mock import AsyncMock, MagicMock, patch

from ophyd.status import Status
from ophyd_async.core.async_status import AsyncStatus
from ophyd_async.epics.motion import Motor

from dodal.devices.util.motor_utils import ExtendedMotor

# def mock_set(motor: Union[ExtendedMotor, Motor], val):
#     motor.setpoint._backend._set_value(val)  # type: ignore
#     motor.readback._backend._set_value(val)  # type: ignore
#     return Status(done=True, success=True)


# def patch_motor(motor: Union[ExtendedMotor, Motor], initial_position=0):
#     motor.setpoint._backend._set_value(initial_position)  # type: ignore
#     motor.readback._backend._set_value(initial_position)  # type: ignore
#     if isinstance(motor, ExtendedMotor):
#         motor.motor_resolution._backend._set_value(0.001)  # type: ignore
#         motor.motor_done_move._backend._set_value(1)  # type: ignore
#     return patch.object(motor, "set", MagicMock(side_effect=partial(mock_set, motor)))


async def mock_good_coroutine():
    return asyncio.sleep(0)


def mock_move(motor: Union[ExtendedMotor, Motor], val, *args, **kwargs):
    motor.setpoint._backend._set_value(val)  # type: ignore
    motor.readback._backend._set_value(val)  # type: ignore
    return mock_good_coroutine()  # type: ignore


def patch_motor(motor: Union[ExtendedMotor, Motor], initial_position=0):
    motor.setpoint._backend._set_value(initial_position)  # type: ignore
    motor.readback._backend._set_value(initial_position)  # type: ignore
    if isinstance(motor, ExtendedMotor):
        motor.motor_resolution._backend._set_value(0.001)  # type: ignore
        motor.motor_done_move._backend._set_value(1)  # type: ignore
    return patch.object(
        motor, "_move", AsyncMock(side_effect=partial(mock_move, motor))
    )
