from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_w

from dodal.log import LOGGER


class HutchNotInterlockedError(Exception):
    def __init__(self, errmsg, *args: object) -> None:
        LOGGER.error(errmsg)
        super().__init__(*args)


class ShutterDemand(str, Enum):
    OPEN = "Open"
    CLOSE = "Close"
    RESET = "Reset"


class ShutterState(str, Enum):
    FAULT = "Fault"
    OPEN = "Open"
    OPENING = "Opening"
    CLOSED = "Closed"
    CLOSING = "Closing"


class HutchInterlock(StandardReadable):
    """Device to check the interlock status of the hutch."""

    def __init__(self, bl_prefix: str, name: str = "") -> None:
        self.status = epics_signal_r(int, bl_prefix + "-PS-IOC-01:M14:LOP")
        super().__init__(name)

    async def is_insterlocked(self) -> bool:
        """If the status value is 0, hutch is interlocked."""
        interlock_state = await self.status.get_value()
        return interlock_state == 0


class HutchShutter(StandardReadable, Movable):
    """Device to operate the hutch shutter.

    If the requested shutter position is "Open", the shutter control PV should first \
    be set to "Reset" in order to reset the interlock state and then move to "Open".
    The reset setp is not needed for closing the shutter.

    When a demand is sent, the device should first check the hutch status \
    and raise an error if it's not interlocked.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_w(ShutterDemand, prefix + "CON")
        self.status = epics_signal_r(ShutterState, prefix + "STA")

        bl_prefix = prefix.split("-")[0]
        self.interlock = HutchInterlock(bl_prefix)

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, position_demand: ShutterDemand):
        interlock_state = await self.interlock.is_insterlocked()
        if not interlock_state:
            raise HutchNotInterlockedError(
                "The hutch is not interlocked, not operating shutter."
            )
        if position_demand == ShutterDemand.OPEN:
            await self.control.set(ShutterDemand.RESET, wait=True)
            await self.control.set(position_demand, wait=True)
            return await wait_for_value(
                self.status, match=ShutterState.OPEN, timeout=DEFAULT_TIMEOUT
            )
        else:
            await self.control.set(position_demand, wait=True)
            return await wait_for_value(
                self.status, match=ShutterState.CLOSED, timeout=DEFAULT_TIMEOUT
            )
