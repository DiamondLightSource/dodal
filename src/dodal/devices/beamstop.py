from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor


class BeamStop(Device):
    x = Cpt(EpicsMotor, "-MO-BS-01:X")
    y = Cpt(EpicsMotor, "-MO-BS-01:Y")
    z = Cpt(EpicsMotor, "-MO-BS-01:Z")
