from ophyd import Component, Device, EpicsSignalRO

from dodal.devices.util.motor_utils import ExtendedEpicsMotor


class Aperture(Device):
    x = Component(ExtendedEpicsMotor, "X")
    y = Component(ExtendedEpicsMotor, "Y")
    z = Component(ExtendedEpicsMotor, "Z")
    small = Component(EpicsSignalRO, "Y:SMALL_CALC")
    medium = Component(EpicsSignalRO, "Y:MEDIUM_CALC")
    large = Component(EpicsSignalRO, "Y:LARGE_CALC")
