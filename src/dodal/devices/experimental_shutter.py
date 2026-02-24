from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    StandardReadable,
    StrictEnum,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_w

from dodal.devices.hutch_shutter import (
    ShutterDemand,
    ShutterNotSafeToOperateError,
    ShutterState,
)

PSS_SHUTTER_1_SUFFIX = "-PS-SHTR-01"
PSS_SHUTTER_2_SUFFIX = "-PS-SHTR-02"


class InterlockState(StrictEnum):
    FAILED = "Failed"
    RUN_ILKS_OK = "Run Ilks Ok"
    OK = "OK"
    DISARMED = "Disarmed"


class ExperimentalShutter(StandardReadable, Movable[ShutterDemand]):
    """Device representing the experimental shutter on a beamline to allow or block
    the beam from reaching the sample. It has some specific interlock conditions that
    must be met before it can be opened.
    """

    def __init__(
        self, bl_prefix: str, shtr_infix: str = PSS_SHUTTER_1_SUFFIX, name: str = ""
    ) -> None:
        self.control = epics_signal_w(ShutterDemand, f"{bl_prefix}{shtr_infix}:CON")
        self.status = epics_signal_r(ShutterState, f"{bl_prefix}{shtr_infix}:STA")
        self.interlock = epics_signal_r(
            InterlockState, f"{bl_prefix}{shtr_infix}:ILKSTA"
        )
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: ShutterDemand):
        if value == ShutterDemand.OPEN:
            interlock_state = await self.interlock.get_value()
            if not interlock_state:
                raise ShutterNotSafeToOperateError(
                    "Interlock state unknown - can not open shutter."
                )
            await self.control.set(ShutterDemand.RESET, wait=True)
            await self.control.set(ShutterDemand.OPEN, wait=True)
            return await wait_for_value(
                self.status, match=ShutterState.OPEN, timeout=DEFAULT_TIMEOUT
            )
        else:
            await self.control.set(value, wait=True)
            return await wait_for_value(
                self.status, match=ShutterState.CLOSED, timeout=DEFAULT_TIMEOUT
            )
