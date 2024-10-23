from enum import IntEnum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_rw


class ColorMode(IntEnum):
    """
    Enum to store the various color modes of the camera. We use RGB1.
    """

    MONO = 0
    BAYER = 1
    RGB1 = 2
    RGB2 = 3
    RGB3 = 4
    YUV444 = 5
    YUV422 = 6
    YUV421 = 7


class Cam(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.color_mode = epics_signal_rw(ColorMode, "GC_BalRatioSelector")
        self.acquire_period = epics_signal_rw(float, "AcquirePeriod")
        self.acquire_time = epics_signal_rw(float, "AcquireTime")
        self.gain = epics_signal_rw(float, "Gain")
        super().__init__(name)
