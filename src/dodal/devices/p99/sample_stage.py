from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw_rbv


class SampleAngleStage(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.theta = epics_signal_rw_rbv(float, prefix + "WRITETHETA", ":RBV")
            self.roll = epics_signal_rw_rbv(float, prefix + "WRITEROLL", ":RBV")
            self.pitch = epics_signal_rw_rbv(float, prefix + "WRITEPITCH", ":RBV")
        super().__init__(name=name)
