from ophyd import Component, Device, EpicsSignal, StatusBase


class BacklightPositioner(Device):
    """Device to control the backlight position."""

    # String description of the backlight position e.g. "In", "OAV2"
    pos_level: EpicsSignal = Component(EpicsSignal, "MP:SELECT")


class DualBacklight(Device):
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

    OUT = "Out"
    IN = "In"

    led1: EpicsSignal = Component(EpicsSignal, "-DI-LED-01:TOGGLE")
    pos1: BacklightPositioner = Component(BacklightPositioner, "-MO-BL-01:")

    led2: EpicsSignal = Component(EpicsSignal, "-DI-LED-02:TOGGLE")

    def set(self, position: str) -> StatusBase:
        status = self.pos1.pos_level.set(position)
        if position == self.OUT:
            status &= self.led1.set("OFF")
        else:
            status &= self.led1.set("ON")
        return status
