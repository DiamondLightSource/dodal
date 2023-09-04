from ophyd import Component, Device, EpicsSignal, StatusBase


class BacklightPositioner(Device):
    """Device to control the backlight position."""

    # String description of the backlight position e.g. "In", "OAV2"
    position: EpicsSignal = Component(EpicsSignal, "MP:SELECT")

    OUT: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ZRST")
    IN: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ONST")
    LoadCheck: EpicsSignal = Component(EpicsSignal, "MP:SELECT.TWST")
    OAV2: EpicsSignal = Component(EpicsSignal, "MP:SELECT.THST")
    Diode: EpicsSignal = Component(EpicsSignal, "MP:SELECT.FRST")

    @property
    def allowed_backlight_positions(self):
        return [
            self.OUT.get(),
            self.IN.get(),
            self.LoadCheck.get(),
            self.OAV2.get(),
            self.Diode.get(),
        ]


class DualBacklight(Device):
    """
    Device to trigger the dual backlight on I24.
    This device is made up by two LEDs:
        - LED1 is the "backlight", can be moved to 5 different positions.
        - LED2 is a "frontlight", it does not move, just switches on and off.
    """

    led1: EpicsSignal = Component(EpicsSignal, "-DI-LED-01:TOGGLE")
    pos1: BacklightPositioner = Component(BacklightPositioner, "-MO-BL-01:")

    led2: EpicsSignal = Component(EpicsSignal, "-DI-LED-02:TOGGLE")

    def set(self, position: str) -> StatusBase:
        status = self.pos1.position.set(position)
        if self.pos1.position.get() == self.pos1.OUT:
            status &= self.led1.set("OFF")
        else:
            status &= self.led1.set("ON")
        return status
