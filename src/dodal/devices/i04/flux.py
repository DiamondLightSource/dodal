from ophyd import Component, Device, EpicsSignalRO, Kind


class Flux(Device):
    """Simple device to get the flux reading"""

    flux_reading: EpicsSignalRO = Component(
        EpicsSignalRO, "SCAT_MAPT", kind=Kind.hinted
    )
