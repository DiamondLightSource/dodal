from unittest.mock import MagicMock

from ophyd_async.core import (
    callback_on_mock_put,
    set_mock_value,
)
from ophyd_async.epics.motion import Motor

from dodal.devices.smargon import Smargon

from .constants import MOCK_ATTRIBUTES_TABLE


def mock_beamline_module_filepaths(bl_name, bl_module):
    if mock_attributes := MOCK_ATTRIBUTES_TABLE.get(bl_name):
        [bl_module.__setattr__(attr[0], attr[1]) for attr in mock_attributes]


def _pass_on_mock(motor, call_log: MagicMock | None = None):
    def _pass_on_mock(value, **kwargs):
        set_mock_value(motor.user_readback, value)
        if call_log is not None:
            call_log(value, **kwargs)

    return _pass_on_mock


def set_smargon_pos(smargon: Smargon, pos: tuple[float, float, float]):
    smargon.x.user_readback.sim_put(pos[0])  # type: ignore
    smargon.y.user_readback.sim_put(pos[1])  # type: ignore
    smargon.z.user_readback.sim_put(pos[2])  # type: ignore


def patch_ophyd_async_motor(
    motor: Motor, initial_position=0, call_log: MagicMock | None = None
):
    """Set some sane defaults, and add a callback to propagate puts to the readback.
    If passed a mock object for call_log, it will call it for all calls to the
    setpoint - useful for testing the order multiple motors are set in.
    """
    set_mock_value(motor.user_setpoint, initial_position)
    set_mock_value(motor.user_readback, initial_position)
    set_mock_value(motor.deadband, 0.001)
    set_mock_value(motor.motor_done_move, 1)
    return callback_on_mock_put(motor.user_setpoint, _pass_on_mock(motor, call_log))
