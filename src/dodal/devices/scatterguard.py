from ophyd import Component as Cpt
from ophyd import Device

from dodal.devices.util.motor_utils import ExtendedEpicsMotor


class Scatterguard(Device):
    x = Cpt(ExtendedEpicsMotor, "X")
    y = Cpt(ExtendedEpicsMotor, "Y")
