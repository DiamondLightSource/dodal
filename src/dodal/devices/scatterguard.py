from ophyd import Component as Cpt
from ophyd import Device

from dodal.devices.util.motor_utils import EpicsMotorWithMRES


class Scatterguard(Device):
    x = Cpt(EpicsMotorWithMRES, "X")
    y = Cpt(EpicsMotorWithMRES, "Y")
