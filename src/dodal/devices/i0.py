from ophyd import Component, Device, EpicsSignalRO, Kind


class I0(Device):
    """XXX not sure if this is actually the right thing or not"""

    intensity: EpicsSignalRO = Component(
        EpicsSignalRO, "-DI-I0M-01:INTENSITY", kind=Kind.normal
    )
