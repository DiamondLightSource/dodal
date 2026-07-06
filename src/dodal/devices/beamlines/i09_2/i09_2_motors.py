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


class PiezoElectricMotor(MovableWithTolerance):
    """A piezoelectric positioning stage with configurable move tolerance.

    This device exposes EPICS signals for readback, setpoint, and motion stop commands.
    Motion completion is determined by comparing the readback and setpoint positions
    using a configurable tolerance.
    """

    def __init__(self, prefix: str, tolerance: float = 0.01, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.user_readback = epics_signal_r(float, prefix + ":POS:RD")

        self.user_setpoint = epics_signal_rw(float, prefix + ":MOV:RD")
        self.tolerance = soft_signal_rw(float, initial_value=tolerance)
        self.motor_stop = epics_signal_w(int, prefix + ":HLT:WR.PROC")
        super().__init__(name=name)

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
