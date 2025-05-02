from ophyd_async.core import (
    StandardReadable,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x


class FilterBValues(StrictEnum):
    DIAMOND_THIN = "Diamond thin"
    DIAMOND_THICK = "Diamond thick"
    NI_DRAIN = "ni drain"
    AU_DRAIN = "au drain"
    AL_DRAIN = "al drain"
    GAP = "Gap"
    IN_LINE_DIODE = "in line diode"

    def __str__(self):
        return self.name.capitalize()


class D7PositionerB(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.setpoint = epics_signal_rw(FilterBValues, prefix + ":SELECT")
            self.done = epics_signal_r(float, prefix + ":DMOV")
            self.stop = epics_signal_x(prefix + ":STOP")
        super().__init__(name=name)
