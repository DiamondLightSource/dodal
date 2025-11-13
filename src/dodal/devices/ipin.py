from ophyd_async.core import StandardReadable, StandardReadableFormat, SubsetEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class IPinGain(SubsetEnum):
    GAIN_10E3_LOW_NOISE = "10^3 low noise"
    GAIN_10E4_LOW_NOISE = "10^4 low noise"
    GAIN_10E5_LOW_NOISE = "10^5 low noise"
    GAIN_10E6_LOW_NOISE = "10^6 low noise"
    GAIN_10E7_LOW_NOISE = "10^7 low noise"
    GAIN_10E8_LOW_NOISE = "10^8 low noise"
    GAIN_10E9_LOW_NOISE = "10^9 low noise"
    GAIN_10E5_HIGH_SPEED = "10^5 high speed"
    GAIN_10E6_HIGH_SPEED = "10^6 high speed"
    GAIN_10E7_HIGH_SPEED = "10^7 high speed"
    GAIN_10E8_HIGH_SPEED = "10^8 high speed"
    GAIN_10E9_HIGH_SPEED = "10^9 high speed"
    GAIN_10E10_HIGH_SPEED = "10^10 high spd"
    GAIN_10E11_HIGH_SPEED = "10^11 high spd"


class IPin(StandardReadable):
    """Simple device to get the ipin reading"""

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(
            format=StandardReadableFormat.HINTED_SIGNAL
        ):
            self.pin_readback = epics_signal_r(float, prefix + "I")
            self.gain = epics_signal_rw(IPinGain, prefix + "GAIN")
        super().__init__(name)
