from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r

from dodal.devices.util.motor_utils import ExtendedMotor


class Aperture(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = ExtendedMotor(prefix + "X")
        self.y = ExtendedMotor(prefix + "Y")
        self.z = ExtendedMotor(prefix + "Z")
        self.small = epics_signal_r(int, prefix + "Y:SMALL_CALC")
        self.medium = epics_signal_r(int, prefix + "Y:MEDIUM_CALC")
        self.large = epics_signal_r(int, prefix + "Y:LARGE_CALC")
        super().__init__(name)
