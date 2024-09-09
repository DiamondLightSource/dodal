from enum import Enum

from ophyd_async.core import Device
from ophyd_async.epics.signal import epics_signal_rw


class SampleAngleStage(Device):
    def __init__(self, prefix: str, name: str):
        self.theta = epics_signal_rw(
            float, prefix + "WRITETHETA:RBV", prefix + "WRITETHETA"
        )
        self.roll = epics_signal_rw(
            float, prefix + "WRITEROLL:RBV", prefix + "WRITEROLL"
        )
        self.pitch = epics_signal_rw(
            float, prefix + "WRITEPITCH:RBV", prefix + "WRITEPITCH"
        )
        super().__init__(name=name)


class p99StageSelections(str, Enum):
    Empty = "Empty"
    Mn5um = "Mn 5um"
    Fe = "Fe (empty)"
    Co5um = "Co 5um"
    Ni5um = "Ni 5um"
    Cu5um = "Cu 5um"
    Zn5um = "Zn 5um"
    Zr = "Zr (empty)"
    Mo = "Mo (empty)"
    Rh = "Rh (empty)"
    Pd = "Pd (empty)"
    Ag = "Ag (empty)"
    Cd25um = "Cd 25um"
    W = "W (empty)"
    Pt = "Pt (empty)"
    User = "User"


class FilterMotor(Device):
    def __init__(self, prefix: str, name: str):
        self.user_setpoint = epics_signal_rw(p99StageSelections, prefix)
        super().__init__(name=name)
