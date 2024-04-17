from ophyd import Component, EpicsMotor, EpicsSignalRO
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r


class ExtendedEpicsMotor(EpicsMotor):
    motor_resolution: Component[EpicsSignalRO] = Component(EpicsSignalRO, ".MRES")
    max_velocity: Component[EpicsSignalRO] = Component(EpicsSignalRO, ".VMAX")
