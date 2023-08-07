from ophyd import Component, Device, EpicsSignal, EpicsSignalRO
from bluesky.protocols import Movable


class SlitMotor(Device, Movable):
    """A class representing a slip motor.
    
    This could be gap, centre, x, y, etc...
    
    Unimplemented signals:
        SPMG
        Anything under "More"
    """
    value: EpicsSignal = Component(EpicsSignal, "VAL")
    readback_value: EpicsSignalRO = Component(EpicsSignalRO, "RBV")
    
    tweak_forward: EpicsSignal = Component(EpicsSignal, "TWF")
    tweak_reverse: EpicsSignal = Component(EpicsSignal, "TWR")
    tweak_value: EpicsSignal = Component(EpicsSignal, "TWV")

    done_moving: EpicsSignalRO = Component(EpicsSignalRO, "DMOV")
    alarm_severity: EpicsSignalRO = Component(EpicsSignalRO, "SEVR")

    stop: EpicsSignal = Component(EpicsSignal, "STOP")
