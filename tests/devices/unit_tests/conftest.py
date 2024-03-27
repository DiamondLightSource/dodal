from functools import partial
from typing import Union
from unittest.mock import MagicMock, patch

from ophyd.epics_motor import EpicsMotor
from ophyd.status import Status
from ophyd_async.epics.motion import Motor

from dodal.devices.util.motor_utils import ExtendedEpicsMotor, ExtendedMotor

# def mock_set(motor: EpicsMotor, val):
#     motor.user_setpoint.sim_put(val)  # type: ignore
#     motor.user_readback.sim_put(val)  # type: ignore
#     return Status(done=True, success=True)


# def patch_motor(motor: Union[EpicsMotor, ExtendedEpicsMotor], initial_position=0):
#     motor.user_setpoint.sim_put(initial_position)  # type: ignore
#     motor.user_readback.sim_put(initial_position)  # type: ignore
#     motor.motor_done_move.sim_put(1)  # type: ignore
#     motor.user_setpoint._use_limits = False
#     if isinstance(motor, ExtendedEpicsMotor):
#         motor.motor_resolution.sim_put(0.001)  # type: ignore
#     return patch.object(motor, "set", MagicMock(side_effect=partial(mock_set, motor)))


def mock_set(motor: Union[ExtendedMotor, Motor], val):
    motor.setpoint._backend._set_value(val)  # type: ignore
    motor.readback._backend._set_value(val)  # type: ignore
    return Status(done=True, success=True)


def patch_motor(motor: Union[ExtendedMotor, Motor], initial_position=0):
    motor.setpoint._backend._set_value(initial_position)  # type: ignore
    motor.readback._backend._set_value(initial_position)  # type: ignore
    motor.motor_done_move._backend._set_value(1)  # type: ignore
    if isinstance(motor, ExtendedMotor):
        motor.motor_resolution._backend._set_value(0.001)  # type: ignore
    return patch.object(motor, "set", MagicMock(side_effect=partial(mock_set, motor)))
