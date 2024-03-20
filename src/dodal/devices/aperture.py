from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class Aperture(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = epics_signal_rw(float, prefix + "X")
        self.y = epics_signal_rw(float, prefix + "Y")
        self.z = epics_signal_rw(float, prefix + "Z")
        self.small = epics_signal_r(int, prefix + "Y:SMALL_CALC")
        self.medium = epics_signal_r(int, prefix + "Y:MEDIUM_CALC")
        self.large = epics_signal_r(int, prefix + "Y:LARGE_CALC")
        super().__init__(name)
