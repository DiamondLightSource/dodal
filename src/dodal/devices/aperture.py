from ophyd import Component, Device, EpicsMotor, EpicsSignalRO


class EpicsMotorWithMRES(EpicsMotor):
    motor_resolution: EpicsSignalRO = Component(EpicsSignalRO, ".MRES")


class Aperture(Device):
    x: EpicsMotor = Component(EpicsMotor, "X")
    y: EpicsMotor = Component(EpicsMotor, "Y")
    z: EpicsMotorWithMRES = Component(EpicsMotorWithMRES, "Z")


class Flux(EpicsSignalRO):
    flux_reading: EpicsSignalRO = Component(EpicsSignalRO, "-MO-MAPT-01:Y:FLUX")
