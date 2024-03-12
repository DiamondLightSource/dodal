from ophyd import Component, Device

from dodal.devices.util.motor_utils import ExtendedEpicsMotor


class Aperture(Device):
    x = Component(ExtendedEpicsMotor, "X")
    y = Component(ExtendedEpicsMotor, "Y")
    z = Component(ExtendedEpicsMotor, "Z")
