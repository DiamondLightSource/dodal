from enum import Enum

from ophyd_async.core import Device
from ophyd_async.epics.signal import epics_signal_rw

from dodal.devices.epics.setReadOnlyMotor import SetReadOnlyMotor


class SampleAngleStage(Device):
    def __init__(self, prefix: str, name: str):
        self.theta = SetReadOnlyMotor(
            prefix, name, suffix=["WRITETHETA", "WRITETHETA:RBV", "WRITETHETA.EGU"]
        )
        self.roll = SetReadOnlyMotor(
            prefix, name, suffix=["WRITETHETA", "WRITETHETA:RBV", "WRITETHETA.EGU"]
        )
        self.pitch = SetReadOnlyMotor(
            prefix, name, suffix=["WRITETHETA", "WRITETHETA:RBV", "WRITETHETA.EGU"]
        )
        super().__init__(name=name)


class p99StageSelections(str, Enum):
    Empty = ("Empty",)
    Mn5um = ("Mn 5um",)
    Fe = ("Fe (empty)",)
    Co5um = ("Co 5um",)
    Ni5um = ("Ni 5um",)
    Cu5um = ("Cu 5um",)
    Zn5um = ("Zn 5um",)
    Zr = ("Zr (empty)",)
    Mo = ("Mo (empty)",)
    Rh = ("Rh (empty)",)
    Pd = ("Pd (empty)",)
    Ag = ("Ag (empty)",)
    Cd25um = ("Cd 25um",)
    W = ("W (empty)",)
    Pt = ("Pt (empty)",)
    User = ("User",)


class FilterMotor(Device):
    def __init__(self, prefix: str, name: str):
        self.user_setpoint = epics_signal_rw(p99StageSelections, prefix)
        super().__init__(name=name)
