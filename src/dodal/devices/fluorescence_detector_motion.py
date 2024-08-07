from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r


class FluorescenceDetectorControlState(Enum):
    OUT = 0
    IN = 1


class FluorescenceDetector(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.pos = epics_signal_r(
                FluorescenceDetectorControlState, "-EA-FLU-01:CTRL"
            )
