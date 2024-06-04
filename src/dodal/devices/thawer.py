from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_rw


class ThawerStates(str, Enum):
    OFF = "Off"
    ON = "On"


class Thawer(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_rw(ThawerStates, prefix + ":CTRL")
        super().__init__(name)
