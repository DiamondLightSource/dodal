from ophyd import Component, Device, EpicsSignal, StatusBase


class BacklightPositioner(Device):
    """Device to control the backlight position."""

    position: EpicsSignal = Component(EpicsSignal, "MP:SELECT")


class DualBlacklight(Device):
    led1: EpicsSignal = Component(EpicsSignal, "-DI-LED-01:TOGGLE")
    pos1: BacklightPositioner = Component(BacklightPositioner, "-MO-BL-01:")

    led2: EpicsSignal = Component(EpicsSignal, "-DI-LED-02:TOGGLE")

    def set(self, pos_to_reach: str) -> StatusBase:
        pass
