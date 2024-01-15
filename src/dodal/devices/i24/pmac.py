from ophyd import Component as Cpt
from ophyd import (
    Device,
    EpicsMotor,
    EpicsSignal,
)


class PMAC(Device):
    """Device to control the chip stage on I24."""

    pmac_string = Cpt(EpicsSignal, "PMAC_STRING")

    x = Cpt(EpicsMotor, "X")
    y = Cpt(EpicsMotor, "Y")
    z = Cpt(EpicsMotor, "Z")

    def home_stages(self):
        self.pmac_string.put(r"\#1hmz\#2hmz\#3hmz", wait=True)
