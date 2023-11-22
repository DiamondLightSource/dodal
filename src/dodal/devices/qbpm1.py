from ophyd import Component as Cpt
from ophyd import Device, EpicsSignalRO, Kind


class QBPM1(Device):
    """Quadrant Beam Position Monitor"""

    intensity: EpicsSignalRO = Cpt(EpicsSignalRO, "-DI-QBPM-01:INTEN", kind=Kind.normal)
    intensityC: EpicsSignalRO = Cpt(
        EpicsSignalRO, "-DI-QBPM-01:INTEN_C", kind=Kind.normal
    )
