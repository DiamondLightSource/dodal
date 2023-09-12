from ophyd import Component, Device, EpicsSignal, StatusBase


class Backlight(Device):
    """Simple device to trigger the pneumatic in/out."""

    OUT = 0
    IN = 1

    pos: EpicsSignal = Component(EpicsSignal, "-EA-BL-01:CTRL")
    # Toggle to switch it On or Off
    toggle: EpicsSignal = Component(EpicsSignal, "-EA-BLIT-01:TOGGLE")

    def set(self, position: int) -> StatusBase:
        status = self.pos.set(position)
        if position == self.OUT:
            status &= self.toggle.set("Off")
        else:
            status &= self.toggle.set("On")
        return status
