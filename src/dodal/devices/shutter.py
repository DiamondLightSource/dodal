from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.signal import epics_signal_rw


class OpenState(Enum):
    CLOSE = 0
    OPEN = 1


class Shutter(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str):
        self.position = epics_signal_rw(
            write_pv=prefix + "CTRL2", read_pv=prefix + "STA", datatype=int, name=name
        )
        super().__init__(name=name)

    def set(self, open_val: int | OpenState):
        if isinstance(open_val, OpenState):
            open_val = open_val.value
        shutter_status: AsyncStatus = self.position.set(open_val)
        return shutter_status
