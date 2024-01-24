from ophyd import Component, Device, EpicsSignalRO, Kind


class Flux(Device):
    """Simple device to get the flux reading"""

    flux_reading = Component(EpicsSignalRO, "SAMP", kind=Kind.hinted)
