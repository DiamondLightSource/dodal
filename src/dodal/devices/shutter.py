from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_rw


class OpenState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    OPENING = "opening"
    CLOSING = "closing"
    FAULT = "fault"


class Shutter(StandardReadable):
    def __init__(self, prefix: str, name: str):
        with self.add_children_as_readables():
            self.position = epics_signal_rw(
                write_pv=prefix + "CTRL2", read_pv=prefix + "STA", datatype=OpenState
            )
        super().__init__(name=name)
