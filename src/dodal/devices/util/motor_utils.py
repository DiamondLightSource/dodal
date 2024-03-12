from ophyd import Component, EpicsMotor, EpicsSignalRO


class ExtendedEpicsMotor(EpicsMotor):
    motor_resolution: Component[EpicsSignalRO] = Component(EpicsSignalRO, ".MRES")
    max_velocity: Component[EpicsSignalRO] = Component(EpicsSignalRO, ".VMAX")
