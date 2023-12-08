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

    def home_stages(self):
        self.pmac_string.set(r"\#1hmz\#2hmz\#3hmz")
