from ophyd import Component as Cpt
from ophyd import (
    Device,
    EpicsMotor,
    EpicsSignal,
)


class PMAC(Device):
    """Device to control the chip stage on I24."""

    pmac_string: EpicsSignal = Cpt(EpicsSignal, "PMAC_STRING")

    x: EpicsMotor = Cpt(EpicsMotor, "X")
    y: EpicsMotor = Cpt(EpicsMotor, "Y")
    z: EpicsMotor = Cpt(EpicsMotor, "Z")
