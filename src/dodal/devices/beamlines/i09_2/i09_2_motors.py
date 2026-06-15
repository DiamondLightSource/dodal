from dataclasses import dataclass
from functools import cached_property

from ophyd_async.core import (
    MovableLogic,
    SignalR,
    SignalW,
    StandardMovable,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    set_and_wait_for_other_value,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w
from ophyd_async.epics.motor import Motor


@dataclass
class PiezoElectricMovableLogic(MovableLogic):
    within_tolerance: SignalR[bool]
    motor_stop: SignalW[int]

    async def move(self, new_position: float, timeout: float | None) -> None:
        await set_and_wait_for_other_value(
            set_signal=self.setpoint,
            set_value=new_position,
            match_signal=self.within_tolerance,
            match_value=True,
            timeout=timeout,
        )

    async def stop(self) -> None:
        await self.motor_stop.set(1)

    # How do provide calculate_timeout without velocity and acceleration?


def _within_threshold_read(setpoint: float, readback: float, deadband: float) -> bool:
    return abs(setpoint - readback) < deadband


class PiezoElectricMotor(StandardMovable[float], StandardReadable):
    """Motor like device with user_readback, user_setpoint, and a stop signals. Has a
    configurable deadband soft signal to configure the tolerance of when a motor is done
    moving. For example, if deadband is configured to be 0.5, and the setpoint is 10 and
    the readback is 9.8, the motor will be done moving and stop blocking for the
    AsyncStatus.
    """

    def __init__(self, prefix: str, deadband: float = 0.01, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.user_readback = epics_signal_r(float, prefix + ":POS:RD")

        self.user_setpoint = epics_signal_rw(float, prefix + ":MOV:RD")
        self.deadband = soft_signal_rw(float, initial_value=deadband)
        self.motor_stop = epics_signal_w(int, prefix + ":HLT:WR.PROC")
        self.within_threshold = derived_signal_r(
            _within_threshold_read,
            deadband=self.deadband,
            setpoint=self.user_setpoint,
            readback=self.user_readback,
        )
        super().__init__(name)

    @cached_property
    def movable_logic(self) -> PiezoElectricMovableLogic:
        return PiezoElectricMovableLogic(
            readback=self.user_readback,
            setpoint=self.user_setpoint,
            within_tolerance=self.within_threshold,
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
