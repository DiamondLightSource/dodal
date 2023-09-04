from ophyd import Component, Device, EpicsSignal, StatusBase


class BacklightPositioner(Device):
    """Device to control the backlight position."""

    # String description of the backlight position e.g. "In", "OAV2"
    pos: EpicsSignal = Component(EpicsSignal, "MP:SELECT")

    zrst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ZRST")  # Out
    onst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ONST")  # In
    twst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.TWST")
    thst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.THST")
    frst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.FRST")

    @property
    def allowed_backlight_positions(self):
        return [
            self.zrst.get(),
            self.onst.get(),
            self.twst.get(),
            self.thst.get(),
            self.frst.get(),
        ]


class DualBacklight(Device):
    """
    Device to trigger the dual backlight on I24.
    This device is made up by two LEDs:
        - LED1 is the "backlight", can be moved to 5 different positions.
        - LED2 is a "frontlight", it does not move, just switches on and off.
    """

    OUT = 0
    IN = 1

    led1: EpicsSignal = Component(EpicsSignal, "-DI-LED-01:TOGGLE")
    pos1: BacklightPositioner = Component(BacklightPositioner, "-MO-BL-01:")

    led2: EpicsSignal = Component(EpicsSignal, "-DI-LED-02:TOGGLE")

    def set(self, position: str) -> StatusBase:
        status = self.pos1.pos.set(position)
        if self.pos1.pos.get() == self.pos1.zrst.get():
            status &= self.led1.set("OFF")
        else:
            status &= self.led1.set("ON")
        return status
