from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor


class GonioLowerStages(Device):
    x = Cpt(EpicsMotor, "-MO-GONP-01:X")
    y = Cpt(EpicsMotor, "-MO-GONP-01:Y")
    z = Cpt(EpicsMotor, "-MO-GONP-01:Z")
