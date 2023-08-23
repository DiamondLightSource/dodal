from ophyd import Component, Device, EpicsSignal


class Backlight(Device):
    """Simple device to trigger the pneumatic in/out"""

    OUT = 0
    IN = 1

    pos: EpicsSignal = Component(EpicsSignal, "CTRL")


class BacklightSwitch(Device):
    """Device to switch backlight on/off"""

    OFF = "Off"
    ON = "On"

    toggle: EpicsSignal = Component(EpicsSignal, "TOGGLE")
