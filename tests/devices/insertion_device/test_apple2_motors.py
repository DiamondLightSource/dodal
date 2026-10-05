from ophyd_async.core import init_devices, soft_signal_rw

from dodal.devices.insertion_device.apple2_motors import MotorStringSetpoint


class MotorStringSetpointImpl(MotorStringSetpoint):
    def __init__(self, name: str = ""):
        self.user_setpoint_str = soft_signal_rw(str, initial_value="0")
        super().__init__(name)


async def test_motor_with_string_setpoint():
    with init_devices(mock=True):
        motor = MotorStringSetpointImpl()

    await motor.user_setpoint.set(5)
    assert await motor.user_setpoint_str.get_value() == "5"

    await motor.user_setpoint_str.set("10")
    assert await motor.user_setpoint.get_value() == 10
