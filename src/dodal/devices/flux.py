from ophyd import Component, Device, EpicsSignalRO


class Flux(Device):
    """Simple device to get the flux reading"""

    flux_reading: EpicsSignalRO = Component(EpicsSignalRO, "FLUX")
