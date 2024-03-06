from ophyd import Component, Device

from dodal.devices.util.motor_utils import EpicsMotorWithMRES


class Aperture(Device):
    x = Component(EpicsMotorWithMRES, "X")
    y = Component(EpicsMotorWithMRES, "Y")
    z = Component(EpicsMotorWithMRES, "Z")
