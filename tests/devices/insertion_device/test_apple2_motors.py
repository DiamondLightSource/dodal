from ophyd_async.core import init_devices

from dodal.devices.insertion_device.apple2_motors import MotorStringSetpoint


async def test_motor_with_string_setpoint():
    with init_devices(mock=True):
        motor = MotorStringSetpoint("TEST:", "")

    await motor.user_setpoint.set(5)
    assert await motor.user_setpoint_str.get_value() == "5"

    await motor.user_setpoint_str.set("10")
    assert await motor.user_setpoint.get_value() == 10
