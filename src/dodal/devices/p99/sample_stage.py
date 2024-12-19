from ophyd_async.core import StandardReadable, SubsetEnum
from ophyd_async.epics.core import epics_signal_rw, epics_signal_rw_rbv


class SampleAngleStage(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.theta = epics_signal_rw_rbv(float, prefix + "WRITETHETA", ":RBV")
            self.roll = epics_signal_rw_rbv(float, prefix + "WRITEROLL", ":RBV")
            self.pitch = epics_signal_rw_rbv(float, prefix + "WRITEPITCH", ":RBV")
        super().__init__(name=name)


class p99StageSelections(SubsetEnum):
    EMPTY = "Empty"
    MN5UM = "Mn 5um"
    FE = "Fe (empty)"
    CO5UM = "Co 5um"
    NI5UM = "Ni 5um"
    CU5UM = "Cu 5um"
    ZN5UM = "Zn 5um"
    ZR = "Zr (empty)"
    MO = "Mo (empty)"
    RH = "Rh (empty)"
    PD = "Pd (empty)"
    AG = "Ag (empty)"
    CD25UM = "Cd 25um"
    W = "W (empty)"
    PT = "Pt (empty)"
    USER = "User"


class FilterMotor(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.user_setpoint = epics_signal_rw(p99StageSelections, prefix)
        super().__init__(name=name)
