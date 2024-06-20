from enum import Enum

from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.signal import epics_signal_rw


class BLPositions(str, Enum):
    OUT = "Out"
    IN = "In"
    LOADCHECK = "LoadCheck"
    OAV2 = "OAV2"
    DIODE = "Diode"


class LedStatus(str, Enum):
    OFF = "OFF"
    ON = "ON"


class BacklightPositioner(StandardReadable):
    """Device to control the backlight position."""

    def __init__(self, prefix: str, name: str = "") -> None:
        # String description of the backlight position e.g. "In", "OAV2"
        self.pos_level = epics_signal_rw(BLPositions, prefix + "MP:SELECT")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, position: BLPositions):
        await self.pos_level.set(position, wait=True)


class DualBacklight(StandardReadable):
    """
    Device to trigger the dual backlight on I24.
    This device is made up by two LEDs:
        - LED1 is the "backlight", can be moved to 5 different positions.
        - LED2 is a "frontlight", it does not move, just switches on and off.

    To set the position for LED1:
        b = DualBacklight(name="backlight)
        b.pos1.pos_level.set("OAV2")

    To see get the available position values for LED1:
        b.pos1.alowed_backlight_positions

    Note that the two LED are independently switched on and off. When LED1 is
    in "Out" position (switched off), LED2 might still be on.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.led1 = epics_signal_rw(LedStatus, prefix + "-DI-LED-01:TOGGLE")
        self.pos1 = BacklightPositioner(prefix + "-MO-BL-01:", name)

        self.led2 = epics_signal_rw(LedStatus, prefix + "-DI-LED-02:TOGGLE")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, position: BLPositions):
        await self.pos1.pos_level.set(position, wait=True)
        if position == BLPositions.OUT:
            await self.led1.set(LedStatus.OFF, wait=True)
        else:
            await self.led1.set(LedStatus.ON, wait=True)
