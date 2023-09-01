from ophyd import Component, Device, EpicsSignal, StatusBase


class BacklightPositioner(Device):
    """Device to control the backlight position."""

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


class DualBlacklight(Device):
    led1: EpicsSignal = Component(EpicsSignal, "-DI-LED-01:TOGGLE")
    pos1: BacklightPositioner = Component(BacklightPositioner, "-MO-BL-01:")

    led2: EpicsSignal = Component(EpicsSignal, "-DI-LED-02:TOGGLE")

    def set(self, pos_to_reach: str) -> StatusBase:
        pass
