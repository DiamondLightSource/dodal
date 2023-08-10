from ophyd import Component, Device, EpicsSignal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from bluesky.protocols import Movable
from enum import IntEnum

from ..status import await_value


class MoveStatus(IntEnum):
    Moving = (0,)
    Stationary = 1


class SlitMotor(Device, Movable):
    """A class representing a slit motor.

    This could be gap, centre, x, y, etc...

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

    done_moving: EpicsSignalRO = Component(EpicsSignalRO, ".DMOV")
    alarm_severity: EpicsSignalRO = Component(EpicsSignalRO, ".SEVR")

    stop_motor: EpicsSignal = Component(EpicsSignal, ".STOP")

    def set(self, target_value) -> SubscriptionStatus:
        await_value(self.done_moving, MoveStatus.Stationary).wait()

        return self.value.set(target_value)
