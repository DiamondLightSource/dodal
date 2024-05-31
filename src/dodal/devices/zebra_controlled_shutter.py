from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_w


class ZebraShutterState(str, Enum):
    CLOSE = "Close"
    OPEN = "Open"


class ZebraShutter(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str):
        self.position_setpoint = epics_signal_w(
            write_pv=prefix + "CTRL2",
            datatype=ZebraShutterState,
        )
        with self.add_children_as_readables():
            self.position_readback = epics_signal_r(
                read_pv=prefix + "STA",
                datatype=ZebraShutterState,
            )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, desired_position: ZebraShutterState):
        await self.position_setpoint.set(desired_position)
        return await wait_for_value(
            signal=self.position_readback,
            match=desired_position,
            timeout=DEFAULT_TIMEOUT,
        )
