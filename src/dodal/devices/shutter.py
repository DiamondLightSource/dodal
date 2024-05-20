from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, wait_for_value
from ophyd_async.epics.signal import epics_signal_r, epics_signal_w


class ShutterSetState(str, Enum):
    CLOSED = "close"
    OPEN = "open"


class ShutterState(str, Enum):
    CLOSED = ShutterSetState.CLOSED
    OPEN = ShutterSetState.OPEN
    OPENING = "opening"
    CLOSING = "closing"
    FAULT = "fault"


class Shutter(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str):
        with self.add_children_as_readables():
            self.position_readback = epics_signal_r(
                read_pv=prefix + "STA",
                datatype=ShutterState,
            )
            self.position_set = epics_signal_w(
                write_pv=prefix + "CTRL2",
                datatype=ShutterSetState,
            )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, position: ShutterSetState):
        new_position = ShutterState(position)
        await self.position_set.set(position)
        return await wait_for_value(
            signal=self.position_readback, match=new_position, timeout=50
        )
