from ophyd import Component, EpicsMotor, EpicsSignalRO
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r


class ExtendedEpicsMotor(EpicsMotor):
    motor_resolution: Component[EpicsSignalRO] = Component(EpicsSignalRO, ".MRES")
    max_velocity: Component[EpicsSignalRO] = Component(EpicsSignalRO, ".VMAX")


class ExtendedMotor(Motor):
    def __init__(self, prefix: str, name: str = ""):
        self.motor_resolution = epics_signal_r(float, prefix + ".MRES")
        self.max_velocity = epics_signal_r(float, prefix + ".VMAX")
        self.motor_done_move = epics_signal_r(float, prefix + ".DMOV")
        super().__init__(name)
