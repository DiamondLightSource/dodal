from ophyd_async.core import StandardReadable
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r


class Aperture(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")
        self.small = epics_signal_r(float, prefix + "Y:SMALL_CALC")
        self.medium = epics_signal_r(float, prefix + "Y:MEDIUM_CALC")
        self.large = epics_signal_r(float, prefix + "Y:LARGE_CALC")
        super().__init__(name)
