from ophyd import Component, Device, EpicsMotor, EpicsSignalRO


class EpicsMotorWithMRES(EpicsMotor):
    motor_resolution: Component[EpicsSignalRO] = Component(EpicsSignalRO, ".MRES")


class Aperture(Device):
    x = Component(EpicsMotor, "X")
    y = Component(EpicsMotor, "Y")
    z = Component(EpicsMotorWithMRES, "Z")
