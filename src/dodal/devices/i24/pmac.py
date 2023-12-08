from ophyd import Component as Cpt
from ophyd import (
    Device,
    EpicsSignal,
)


class PMAC(Device):
    """Device to control the chip stage on I24."""

    pmac_string: EpicsSignal = Cpt(EpicsSignal, "PMAC_STRING")

    x: EpicsSignal = Cpt(EpicsSignal, "X")
    y: EpicsSignal = Cpt(EpicsSignal, "Y")
    z: EpicsSignal = Cpt(EpicsSignal, "Z")

    def home_stages(self):
        self.pmac_string.set(r"\#1hmz\#2hmz\#3hmz")
