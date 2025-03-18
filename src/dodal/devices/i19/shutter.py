from enum import Enum

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.hutch_shutter import HutchShutter, ShutterDemand
from dodal.log import LOGGER


class HutchInvalidError(Exception):
    pass


class HutchState(str, Enum):
    EH1 = "EH1"
    EH2 = "EH2"
    INVALID = "INVALID"


class AccessControlledShutter(StandardReadable, Movable):
    def __init__(self, prefix: str, hutch: HutchState, name: str = "") -> None:
        self.hutch_state = epics_signal_r(str, f"{prefix}:EHStatus.VALA")
        self.hutch_request = hutch
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: ShutterDemand):
        pass


class HutchConditionalShutter(StandardReadable, Movable):
    """ I19-specific device to operate the hutch shutter.

    This device evaluates the hutch state value to work out which of the two I19 \
    hutches is in use and then implements the HutchShutter device to operate the \
    experimental shutter.
    As the two hutches are located in series, checking the hutch in use is necessary to \
    avoid accidentally operating the shutter from one hutch while the other has beamtime.

    The hutch name should be passed to the device upon instantiation. If this does not \
    coincide with the current hutch in use, a warning will be logged and the shutter \
    will not be operated. This is to allow for testing of plans.
    An error will instead be raised if the hutch state reads as "INVALID".
    """

    def __init__(self, prefix: str, hutch: HutchState, name: str = "") -> None:
        self.shutter = HutchShutter(prefix=prefix, name=name)
        bl_prefix = prefix.split("-")[0]
        self.hutch_state = epics_signal_r(str, f"{bl_prefix}-OP-STAT-01:EHStatus.VALA")
        self.hutch_request = hutch
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: ShutterDemand):
        hutch_in_use = await self.hutch_state.get_value()
        LOGGER.info(f"Current hutch in use: {hutch_in_use}")
        if hutch_in_use == HutchState.INVALID:
            raise HutchInvalidError(
                "The hutch state is invalid. Contact the beamline staff."
            )
        if hutch_in_use != self.hutch_request:
            # NOTE Warn but don't fail
            LOGGER.warning(
                f"{self.hutch_request} is not the hutch in use. Shutter will not be operated."
            )
        else:
            await self.shutter.set(value)
