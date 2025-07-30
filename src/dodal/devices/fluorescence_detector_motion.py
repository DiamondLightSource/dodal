from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r

from dodal.common.enums import InOut


class FluorescenceDetector(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.pos = epics_signal_r(InOut, prefix + "-EA-FLU-01:CTRL")
        super().__init__(name)
