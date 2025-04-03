from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    StandardReadable,
    StrictEnum,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_w

from dodal.log import LOGGER

HUTCH_SAFE_FOR_OPERATIONS = 0  # Hutch is locked and can't be entered


# Enable to allow testing when the beamline is down, do not change in production!
TEST_MODE = False
# will be made more generic in https://github.com/DiamondLightSource/dodal/issues/754


class ShutterNotSafeToOperateError(Exception):
    pass


class ShutterDemand(StrictEnum):
    OPEN = "Open"
    CLOSE = "Close"
    RESET = "Reset"


class ShutterState(StrictEnum):
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

    # TODO replace with read
    # See https://github.com/DiamondLightSource/dodal/issues/651
    async def shutter_safe_to_operate(self) -> bool:
        """If the status value is 0, hutch has been searched and locked and it is safe \
        to operate the shutter.
        If the status value is not 0 (usually set to 7), the hutch is open and the \
        shutter should not be in use.
        """
        interlock_state = await self.status.get_value()
        return interlock_state == HUTCH_SAFE_FOR_OPERATIONS


class HutchShutter(StandardReadable, Movable[ShutterDemand]):
    """Device to operate the hutch shutter.

    When a demand is sent, the device should first check the hutch status \
    and raise an error if it's not interlocked (searched and locked), meaning it's not \
    safe to operate the shutter.

    If the requested shutter position is "Open", the shutter control PV should first \
    go to "Reset" and then move to "Open". This is because before opening the hutch \
    shutter, the interlock status PV (`-PS-SHTR-01:ILKSTA`) will show as `failed` until \
    the hutch shutter is reset. This will set the interlock status to `OK`, allowing \
    for shutter operations. Until this step is done, the hutch shutter can't be opened.
    The reset is not needed for closing the shutter.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_w(ShutterDemand, f"{prefix}CON")
        self.status = epics_signal_r(ShutterState, f"{prefix}STA")

        bl_prefix = prefix.split("-")[0]
        self.interlock = HutchInterlock(bl_prefix)

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: ShutterDemand):
        interlock_state = await self.interlock.shutter_safe_to_operate()
        if not interlock_state and not TEST_MODE:
            # If not in test mode, fail. If in test mode, the optics hutch may be open.
            raise ShutterNotSafeToOperateError(
                "The hutch has not been locked, not operating shutter."
            )
        if not TEST_MODE:
            if value == ShutterDemand.OPEN:
                await self.control.set(ShutterDemand.RESET, wait=True)
                await self.control.set(value, wait=True)
                return await wait_for_value(
                    self.status, match=ShutterState.OPEN, timeout=DEFAULT_TIMEOUT
                )
            else:
                await self.control.set(value, wait=True)
                return await wait_for_value(
                    self.status, match=ShutterState.CLOSED, timeout=DEFAULT_TIMEOUT
                )
        else:
            LOGGER.warning(
                "Running in test mode, will not operate the experiment shutter."
            )
