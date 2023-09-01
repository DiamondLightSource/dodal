from ophyd import Component, Device, EpicsSignal


class Backlight(Device):
    """Simple device to trigger the pneumatic in/out."""

    OUT = 0
    IN = 1

    pos: EpicsSignal = Component(EpicsSignal, "-EA-BL-01:CTRL")
    # Toggle to switch it On or Off
    toggle: EpicsSignal = Component(EpicsSignal, "-EA-BLIT-01:TOGGLE")

    def set(self, position: int):
        self.pos.set(position)
        if self.pos.get() == self.OUT:
            self.toggle.set("Off")
        else:
            self.toggle.set("On")
