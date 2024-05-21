from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, wait_for_value
from ophyd_async.epics.signal import epics_signal_r, epics_signal_w


class ShutterSetState(str, Enum):
    CLOSE = "Close"
    OPEN = "Open"
    RESET = "Reset"


class ShutterState(str, Enum):
    CLOSED = "Closed"
    OPEN = "Open"
    OPENING = "Opening"
    CLOSING = "Closing"
    FAULT = "Fault"


class Shutter(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str):
        self.position_set = epics_signal_w(
            write_pv=prefix + "CTRL2",
            datatype=ShutterSetState,
        )
        with self.add_children_as_readables():
            self.position_readback = epics_signal_r(
                read_pv=prefix + "STA",
                datatype=ShutterState,
            )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, desired_position: ShutterSetState):
        if desired_position == ShutterSetState.RESET:
            return
        new_position = (
            ShutterState.CLOSED
            if desired_position == ShutterSetState.CLOSE
            else ShutterState.OPEN
        )
        await self.position_set.set(desired_position)
        return await wait_for_value(
            signal=self.position_readback, match=new_position, timeout=50
        )
