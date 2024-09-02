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


class ZebraShutterControl(str, Enum):
    MANUAL = "Manual"
    AUTO = "Auto"


class ZebraShutter(StandardReadable, Movable):
    """The shutter on most MX beamlines is controlled by the zebra.

    Internally in the zebra there are two AND gates, one for manual control and one for
    automatic control. A soft input (aliased to control) will switch between
    which of these AND gates to use. For the manual gate the shutter is then controlled
    by a different soft input (aliased to position_setpoint). Both these AND gates then
    feed into an OR gate, which then feeds to the shutter."""

    def __init__(self, prefix: str, name: str):
        self.position_setpoint = epics_signal_w(ZebraShutterState, prefix + "CTRL2")
        self.control = epics_signal_w(ZebraShutterControl, prefix + "CTRL1")

        with self.add_children_as_readables():
            self.position_readback = epics_signal_r(ZebraShutterState, prefix + "STA")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: ZebraShutterState):
        await self.position_setpoint.set(value)
        return await wait_for_value(
            signal=self.position_readback,
            match=value,
            timeout=DEFAULT_TIMEOUT,
        )
