import asyncio
from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, wait_for_value
from ophyd_async.epics.signal import epics_signal_r, epics_signal_w


class OpenStateSet(str, Enum):
    CLOSED = "close"
    OPEN = "open"


class OpenStateReadback(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    OPENING = "opening"
    CLOSING = "closing"
    FAULT = "fault"


class Shutter(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str):
        with self.add_children_as_readables():
            self.position_readback = epics_signal_r(
                read_pv=prefix + "STA",
                datatype=OpenStateReadback,
            )
            self.position_set = epics_signal_w(
                write_pv=prefix + "CTRL2",
                datatype=OpenStateSet,
            )
        super().__init__(name=name)

    def set(self, position: OpenStateSet):

        return AsyncStatus(
            asyncio.wait_for(
                await wait_for_value(self.position_readback, position, None), timeout=5
            )
        )
