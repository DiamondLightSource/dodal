from abc import ABC, abstractmethod
from math import isclose

from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    EnumTypes,
    SignalR,
    StandardReadable,
    StrictEnum,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_w

from dodal.log import LOGGER

HUTCH_SAFE_FOR_OPERATIONS = 0  # Hutch is locked and can't be entered
PSS_SHUTTER_SUFFIX = "-PS-IOC-01:M14:LOP"
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


class BaseHutchInterlock(ABC, StandardReadable):
    status: SignalR[float | EnumTypes]
    bl_prefix: str

    def __init__(
        self,
        signal_type: type[EnumTypes] | type[float],
        bl_prefix: str,
        interlock_infix: str,
        interlock_suffix: str,
        name: str = "",
    ) -> None:
        pv_address = f"{bl_prefix}{interlock_infix}{interlock_suffix}"
        with self.add_children_as_readables():
            self.status = epics_signal_r(signal_type, pv_address)
        super().__init__(name)

    @abstractmethod
    async def shutter_safe_to_operate(self) -> bool:
        """Abstract method to define if interlock allows shutter to operate."""


class HutchInterlock(BaseHutchInterlock):
    """Device to check the interlock status of the hutch using PSS pv."""

    def __init__(
        self,
        bl_prefix: str,
        shtr_infix: str = "",
        interlock_suffix: str = PSS_SHUTTER_SUFFIX,
        name: str = "",
    ) -> None:
        super().__init__(
            signal_type=float,
            bl_prefix=bl_prefix,
            interlock_infix=shtr_infix,
            interlock_suffix=interlock_suffix,
            name=name,
        )

    # TODO replace with read
    # See https://github.com/DiamondLightSource/dodal/issues/651
    async def shutter_safe_to_operate(self) -> bool:
        """If the status value is 0, hutch has been searched and locked and it is safe \
        to operate the shutter.
        If the status value is not 0 (usually set to 7), the hutch is open and the \
        shutter should not be in use.
        """
        interlock_state = await self.status.get_value()
        return isclose(float(interlock_state), HUTCH_SAFE_FOR_OPERATIONS, abs_tol=5e-2)


class BaseHutchShutter(StandardReadable, Movable[ShutterDemand]):
    """Device to operate the hutch shutter.

    Base class for HutchShutters - extended by some that do not use an interlock
    and by others that do.  See child classes for details
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
            await self._shutter_action(value)

    async def _shutter_action(self, value: ShutterDemand):
        await self.control.set(value)
        return await wait_for_value(self.status, match=value, timeout=DEFAULT_TIMEOUT)

    async def _pre_open_shutter_actions(self):
        pass  # implemented in child class

    def _test_mode_set(self):
        LOGGER.warning("Running in test mode, will not operate the experiment shutter.")


class HutchShutter(BaseHutchShutter):
    """Device to operate the hutch shutter.  Without an interlock.

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
        super().__init__(name, f"{bl_prefix}{shtr_infix}")

    async def _pre_open_shutter_actions(self):
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
    """

    def __init__(
        self,
        bl_prefix: str,
        interlock: BaseHutchInterlock,
        shtr_infix: str = EXP_SHUTTER_1_INFIX,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.interlock = interlock
        super().__init__(name, f"{bl_prefix}{shtr_infix}")

    async def _pre_open_shutter_actions(self):
        await self._check_interlock()
        await self.control.set(ShutterDemand.RESET)

    async def _check_interlock(self):
        interlock_state = await self.interlock.shutter_safe_to_operate()
        if not interlock_state:
            raise ShutterNotSafeToOperateError(
                "The hutch has not been locked, not operating shutter."
            )
