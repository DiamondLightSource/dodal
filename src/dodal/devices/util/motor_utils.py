from ophyd import Component, EpicsMotor, EpicsSignalRO


class EpicsMotorWithMRES(EpicsMotor):
    motor_resolution: Component[EpicsSignalRO] = Component(EpicsSignalRO, ".MRES")
