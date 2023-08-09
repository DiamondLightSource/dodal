from ophyd import Component, Device, EpicsSignal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from bluesky.protocols import Movable, Readable
from enum import IntEnum
from collections import OrderedDict

from ..status import await_value


class MoveStatus(IntEnum):
    Moving = (0,)
    Stationary = 1


class SlitMotor(Device, Movable, Readable):
    """A class representing a slit motor.

    This could be gap, centre, x, y, etc...
    By default sets to .VAL and reads from .RBV

    Unimplemented signals:
        SPMG
        KILL
        Anything under "More"
    """

    value: EpicsSignal = Component(EpicsSignal, ".VAL")
    readback_value: EpicsSignalRO = Component(EpicsSignalRO, ".RBV")

    tweak_forward: EpicsSignal = Component(EpicsSignal, ".TWF")
    tweak_reverse: EpicsSignal = Component(EpicsSignal, ".TWR")
    tweak_value: EpicsSignal = Component(EpicsSignal, ".TWV")

    done_moving: EpicsSignalRO = Component(EpicsSignalRO, "DMOV")
    alarm_severity: EpicsSignalRO = Component(EpicsSignalRO, "SEVR")

    stop_motor: EpicsSignal = Component(EpicsSignal, ".STOP")

    def set(self, target_value) -> SubscriptionStatus:
        """Set .VAL to target_value, making sure motor is idle at start of operation.

        Parameters:
            target_value: Value written to .VAL

        Returns:
            A SubscriptionStatus marked complete when motor is idle after operation."""
        await_value(self.done_moving, MoveStatus.Stationary).wait()

        status = self.value.set(target_value)

        await_value(self.done_moving, MoveStatus.Moving).wait()

        status &= await_value(self.done_moving, MoveStatus.Stationary)

        return status

    def read(self):
        await_value(self.done_moving, MoveStatus.Stationary).wait()

        return self.readback_value.read()

    def describe(self) -> OrderedDict:
        od = OrderedDict()

        od[self.name + "_readback_value"] = {
            "source": self.readback_value.name,
            "dtype": "number",
            "shape": [],
        }

        return od
