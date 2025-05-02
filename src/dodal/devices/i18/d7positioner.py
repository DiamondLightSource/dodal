from ophyd_async.core import (
    StandardReadable,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x


class FilterAValues(StrictEnum):
    """Maps from a short usable name to the string name in EPICS"""

    AL_2MM = "2 mm Al"
    AL_1_5MM = "1.5 mm Al"
    AL_1_25MM = "1.25 mm Al"
    AL_0_8MM = "0.8 mm Al"
    AL_0_55MM = "0.55 mm Al"
    AL_0_5MM = "0.5 mm Al"
    AL_0_3MM = "0.3 mm Al"
    AL_0_25MM = "0.25 mm Al"
    AL_0_15MM = "0.15 mm Al"
    AL_0_1MM = "0.1 mm Al"
    AL_0_025MM = "0.025 mm Al"
    AL_GAP = "Gap"

    def __str__(self):
        return self.name.capitalize()


class D7PositionerA(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.setpoint = epics_signal_rw(FilterAValues, prefix + ":SELECT")
            self.done = epics_signal_r(float, prefix + ":DMOV")
            self.stop = epics_signal_x(prefix + ":STOP")
        super().__init__(name=name)


