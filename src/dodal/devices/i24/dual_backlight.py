from ophyd_async.core import AsyncStatus, StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw


class BacklightPositions(StrictEnum):
    OUT = "Out"
    IN = "In"
    LOAD_CHECK = "LoadCheck"
    OAV2 = "OAV2"
    DIODE = "Diode"
    WHITE_IN = "White In"


class LEDStatus(StrictEnum):
    OFF = "OFF"
    ON = "ON"


class BacklightPositioner(StandardReadable):
    """Device to control the backlight position."""

    def __init__(self, prefix: str, name: str = "") -> None:
        # Enum description of the backlight position e.g. "In", "OAV2"
        self.pos_level = epics_signal_rw(BacklightPositions, prefix + "MP:SELECT")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: BacklightPositions):
        await self.pos_level.set(value, wait=True)


class DualBacklight(StandardReadable):
    """
    Device to trigger the dual backlight on I24.
    This device is made up by two LEDs:
        - LED1 is the "backlight", can be moved to 5 different positions.
        - LED2 is a "frontlight", it does not move, just switches on and off.

    To set the position for LED1:
        b = DualBacklight(name="backlight)
        b.backlight_position.set("OAV2")

    Note that the two LED are independently switched on and off. When LED1 is
    in "Out" position (switched off), LED2 might still be on.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.backlight_state = epics_signal_rw(LEDStatus, prefix + "-DI-LED-01:TOGGLE")
        self.backlight_position = BacklightPositioner(prefix + "-MO-BL-01:", name)

        self.frontlight_state = epics_signal_rw(LEDStatus, prefix + "-DI-LED-02:TOGGLE")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: BacklightPositions):
        await self.backlight_position.set(value)
        if value == BacklightPositions.OUT:
            await self.backlight_state.set(LEDStatus.OFF, wait=True)
        else:
            await self.backlight_state.set(LEDStatus.ON, wait=True)
