import enum
from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x


class D7Positioner(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.setpoint = epics_signal_rw(enum, prefix + ":SELECT")
            self.done = epics_signal_r(float, prefix + ":DMOV")
            self.stop = epics_signal_x( prefix + ":STOP")
        super().__init__(name=name)
