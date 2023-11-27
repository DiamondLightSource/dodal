from ophyd import Component as Cpt
from ophyd import (
    Device,
    EpicsSignal,  # EpicsMotor
)


class PMAC(Device):
    pmac_string: EpicsSignal = Cpt(EpicsSignal, "PMAC_STRING")
