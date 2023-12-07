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

    def home_stages(self, direction: str):
        # uses from ophyd.epics_motor import HomeEnum: forward or reverse (?)
        # I think I shuld just be able to pass "forward" or "reverse"
        # but which?
        self.x.home(direction)
        self.y.home(direction)
        self.z.home(direction)
