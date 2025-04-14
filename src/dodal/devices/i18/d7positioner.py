from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class D7Positioner(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        self._prefix = prefix
        with self.add_children_as_readables():
            self.setpoint = epics_signal_rw(float, prefix + ":SELECT")
            self.readback = epics_signal_r(float, prefix + ":SELECT")
            self.done = epics_signal_r(float, prefix + ":DMOV")
            self.stop = epics_signal_rw(bool, prefix + ":STOP.PROC")
        super().__init__(name=name)
