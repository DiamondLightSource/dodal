from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r


class FluorescenceDetectorControlState(StrictEnum):
    OUT = "Out"
    IN = "In"


class FluorescenceDetector(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.pos = epics_signal_r(
                FluorescenceDetectorControlState, prefix + "-EA-FLU-01:CTRL"
            )
        super().__init__(name)
