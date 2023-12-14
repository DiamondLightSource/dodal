from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor


class Scatterguard(Device):
    x = Cpt(EpicsMotor, "X")
    y = Cpt(EpicsMotor, "Y")
