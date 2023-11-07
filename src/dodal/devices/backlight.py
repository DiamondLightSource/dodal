from ophyd import Component, Device, EpicsSignal, StatusBase


class Backlight(Device):
    """Simple device for i03 to trigger the pneumatic in/out."""

    OUT = 0
    IN = 1

    pos: EpicsSignal = Component(EpicsSignal, "-EA-BL-01:CTRL")
    toggle: EpicsSignal = Component(EpicsSignal, "-EA-BLIT-01:TOGGLE")

    def set(self, position: int) -> StatusBase:
        status = self.pos.set(position)
        if position == self.OUT:
            status &= self.toggle.set("Off")
        else:
            status &= self.toggle.set("On")
        return status


class VmxmBacklight(Device):
    """Simple device for VMXm to control the backlight."""

    OUT = 0
    IN = 1

    pos: EpicsSignal = Component(EpicsSignal, "-DI-IOC-02:LED:INOUT")
    toggle: EpicsSignal = Component(EpicsSignal, "-EA-OAV-01:FZOOM:TOGGLE")

    def set(self, position: int) -> StatusBase:
        status = self.pos.set(position)
        if position == self.OUT:
            status &= self.toggle.set("Off")
        else:
            status &= self.toggle.set("On")
        return status
