from abc import ABC, abstractmethod

from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    StandardReadable,
    StrictEnum,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_w

from dodal.devices.interlocks import BaseInterlock
from dodal.log import LOGGER

EXP_SHUTTER_1_INFIX = "-PS-SHTR-01"
EXP_SHUTTER_2_INFIX = "-PS-SHTR-02"

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


class BaseHutchShutter(ABC, StandardReadable, Movable[ShutterDemand]):
    """Device to operate the hutch shutter.

    Base class for HutchShutters - extended by some that do not use an interlock
    and by others that do.  See child classes for details

    Attributes:
        control: An writeable EPICS signal to drive the shutter state changes
        status: A readable EPICS signal to read the present shutter state
    """

    def __init__(
        self,
        bl_shutter_prefix: str,
        name: str = "",
    ) -> None:
        self.control = epics_signal_w(ShutterDemand, f"{bl_shutter_prefix}:CON")
        with self.add_children_as_readables():
            self.status = epics_signal_r(ShutterState, f"{bl_shutter_prefix}:STA")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: ShutterDemand):
        if TEST_MODE:
            self._test_mode_set()
        else:
            if value == ShutterDemand.OPEN:
                await self._pre_open_shutter_actions()
                required_match: ShutterState = ShutterState.OPEN
            else:
                required_match: ShutterState = ShutterState.CLOSED
            await self._shutter_action(value=value, required_match=required_match)

    @abstractmethod
    async def _pre_open_shutter_actions(self):
        """Provides internal implementation of pre-requisite steps that support opening of the shutter."""

    async def _shutter_action(self, value: ShutterDemand, required_match: ShutterState):
        await self.control.set(value)
        await wait_for_value(self.status, match=required_match, timeout=DEFAULT_TIMEOUT)

    def _test_mode_set(self):
        LOGGER.warning("Running in test mode, will not operate the experiment shutter.")


class HutchShutter(BaseHutchShutter):
    """Device to operate the hutch shutter.

    When a demand is sent, the shutter can be operated without checking
    the hutch status, instead relying on default shutter interlock (:ILKSTA).

    If the requested shutter position is "Open", the shutter control PV should first
    go to "Reset" and then move to "Open". This is because before opening the hutch
    shutter, the interlock status will show as `failed` until the hutch shutter is
    reset. The reset will set the interlock status to `OK`, allowing for shutter operations.
    Until this step is done, the hutch shutter can't be opened. The reset is not needed
    for closing the shutter.
    """

    def __init__(
        self,
        bl_prefix: str,
        shtr_infix: str = EXP_SHUTTER_1_INFIX,
        name: str = "",
    ) -> None:
        super().__init__(f"{bl_prefix}{shtr_infix}", name)

    async def _pre_open_shutter_actions(self):
        """Required by parent class API - resets the shutter prior to opening."""
        await self.control.set(ShutterDemand.RESET)


class InterlockedHutchShutter(BaseHutchShutter):
    """Device to operate the hutch shutter.  With an interlock.

    When a demand is sent the device should first check the hutch status and
    raise an error if it's not interlocked (searched and locked), as not interlocked
    means it's not safe to operate the shutter.

    If the requested shutter position is "Open", the shutter control PV should first
    go to "Reset" and then move to "Open". This is because before opening the hutch
    shutter, the interlock status will show as `failed` until the hutch shutter is
    reset. The reset will set the interlock status to `OK`, allowing for shutter operations.
    Until this step is done, the hutch shutter can't be opened. The reset is not needed
    for closing the shutter.

    Attributes:
        interlock : Hutch PSS based interlock status checker
    """

    def __init__(
        self,
        bl_prefix: str,
        interlock: BaseInterlock,
        shtr_infix: str = EXP_SHUTTER_1_INFIX,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.interlock = interlock
        super().__init__(f"{bl_prefix}{shtr_infix}", name)

    async def _pre_open_shutter_actions(self):
        """Required by parent class API - checks interlock, then resets the shutter prior to opening."""
        await self._check_interlock()
        await self.control.set(ShutterDemand.RESET)

    async def _check_interlock(self):
        """Disrupts shutter opening if the interlock is not in a safe to operate state.

        Raises:
             ShutterNotSafeToOperateError - whereby an unhappy interlock will veto any attempt to open the shutter.
        """
        interlock_state = await self.interlock.is_safe.get_value()
        if not interlock_state:
            raise ShutterNotSafeToOperateError(
                "The hutch has not been locked, not operating shutter."
            )
