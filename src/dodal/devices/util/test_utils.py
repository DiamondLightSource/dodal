from contextlib import ExitStack

from ophyd_async.core import Device
from ophyd_async.epics.motor import Motor
from ophyd_async.testing import (
    callback_on_mock_put,
    set_mock_value,
)


def patch_motor(motor: Motor, initial_position=0):
    set_mock_value(motor.user_setpoint, initial_position)
    set_mock_value(motor.user_readback, initial_position)
    set_mock_value(motor.deadband, 0.001)
    set_mock_value(motor.motor_done_move, 1)
    set_mock_value(motor.velocity, 3)
    set_mock_value(motor.max_velocity, 5)
    return callback_on_mock_put(
        motor.user_setpoint,
        lambda pos, *args, **kwargs: set_mock_value(motor.user_readback, pos),
    )


def patch_all_motors(parent_device: Device):
    motors = []

    def recursively_find_motors(device: Device):
        for _, child_device in device.children():
            if isinstance(child_device, Motor):
                motors.append(child_device)
            recursively_find_motors(child_device)

    recursively_find_motors(parent_device)
    motor_patch_stack = ExitStack()
    for motor in motors:
        motor_patch_stack.enter_context(patch_motor(motor))
    return motor_patch_stack
