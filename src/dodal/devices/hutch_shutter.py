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

HUTCH_SAFE_FOR_OPERATIONS = 0  # Hutch is locked and can't be entered


class ShutterNotSafeToOperateError(Exception):
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
        self.status = epics_signal_r(float, bl_prefix + "-PS-IOC-01:M14:LOP")
        super().__init__(name)

    async def shutter_safe_to_operate(self) -> bool:
        """If the status value is 0, hutch has been searched and locked and it is safe \
        to operate the shutter.
        If the status value is not 0 (usually set to 7), the hutch is open and the \
        shutter should not be in use.
        """
        interlock_state = await self.status.get_value()
        return interlock_state == HUTCH_SAFE_FOR_OPERATIONS


class HutchShutter(StandardReadable, Movable):
    """Device to operate the hutch shutter.

    When a demand is sent, the device should first check the hutch status \
    and raise an error if it's not interlocked (searched and locked), meaning it's not \
    safe to operate the shutter.

    If the requested shutter position is "Open", the shutter control PV should first \
    be set to "Reset" and then move to "Open". This is because before opening the hutch \
    shutter, the interlock status PV (`-PS-SHTR-01:ILKSTA`). Resetting the shutter will \
    set this status to `OK`, allowing for shutter operations. Until this step is done, \
    the hutch shutter can't be opened. The reset is not needed for closing the shutter.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_w(ShutterDemand, prefix + "CON")
        self.status = epics_signal_r(ShutterState, prefix + "STA")

        bl_prefix = prefix.split("-")[0]
        self.interlock = HutchInterlock(bl_prefix)

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, position_demand: ShutterDemand):
        interlock_state = await self.interlock.shutter_safe_to_operate()
        if not interlock_state:
            raise ShutterNotSafeToOperateError(
                "The hutch has not been locked, not operating shutter."
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
