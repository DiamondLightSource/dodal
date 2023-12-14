from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor


class Scintillator(Device):
    y = Cpt(EpicsMotor, "-MO-SCIN-01:Y")
    z = Cpt(EpicsMotor, "-MO-SCIN-01:Z")
