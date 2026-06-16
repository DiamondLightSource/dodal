from dataclasses import dataclass
from functools import cached_property

from ophyd_async.core import (
    SignalW,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w
from ophyd_async.epics.motor import Motor

from dodal.devices.movable import MovableWithTolerance, MovableWithToleranceLogic


@dataclass
class PiezoElectricMovableLogic(MovableWithToleranceLogic):
    motor_stop: SignalW[int]

    async def stop(self) -> None:
        await self.motor_stop.set(1)

    # How do provide calculate_timeout without velocity and acceleration?


class PiezoElectricMotor(MovableWithTolerance):
    """Motor like device with user_readback, user_setpoint, and a stop signals. Has a
    configurable deadband soft signal to configure the tolerance of when a motor is done
    moving. For example, if deadband is configured to be 0.5, and the setpoint is 10 and
    the readback is 9.8, the motor will be done moving and stop blocking for the
    AsyncStatus.
    """

    def __init__(self, prefix: str, tolerance: float = 0.01, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.user_readback = epics_signal_r(float, prefix + ":POS:RD")

        self.user_setpoint = epics_signal_rw(float, prefix + ":MOV:RD")
        self.tolerance = soft_signal_rw(float, initial_value=tolerance)
        self.motor_stop = epics_signal_w(int, prefix + ":HLT:WR.PROC")
        super().__init__(
            tolerance=self.tolerance,
            setpoint=self.user_setpoint,
            readback=self.user_readback,
            name=name,
        )

    @cached_property
    def movable_logic(self) -> PiezoElectricMovableLogic:
        return PiezoElectricMovableLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            within_tolerance=self.within_tolerance,
            motor_stop=self.motor_stop,
        )


class I092SampleManipulator(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x1 = PiezoElectricMotor(prefix + "X1")
            self.x2 = PiezoElectricMotor(prefix + "X2")
            self.x3 = PiezoElectricMotor(prefix + "X3")
            self.y = PiezoElectricMotor(prefix + "Y")
            self.z1 = PiezoElectricMotor(prefix + "Z1")
            self.z2 = PiezoElectricMotor(prefix + "Z2")

            self.xc = Motor(prefix + "X")
            self.zc = Motor(prefix + "Z")

        super().__init__(name)
