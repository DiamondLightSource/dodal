from ophyd_async.core import StandardReadable, SubsetEnum
from ophyd_async.epics.core import epics_signal_rw, epics_signal_rw_rbv


class SampleAngleStage(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.theta = epics_signal_rw_rbv(float, prefix + "WRITETHETA", ":RBV")
            self.roll = epics_signal_rw_rbv(float, prefix + "WRITEROLL", ":RBV"))
            self.pitch = epics_signal_rw_rbv(float, prefix + "WRITEPITCH",":RBV"))
        super().__init__(name=name)


class p99StageSelections(SubsetEnum):
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


class FilterMotor(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.user_setpoint = epics_signal_rw(p99StageSelections, prefix)
        super().__init__(name=name)
