from ophyd import Component as Cpt
from ophyd import (
    Device,
    EpicsSignal,
)


class PMAC(Device):
    """Device to control the chip stage on I24."""

    pmac_string: EpicsSignal = Cpt(EpicsSignal, "PMAC_STRING")
