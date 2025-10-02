from ophyd_async.core import StandardReadable, StandardReadableFormat, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class V2FGain(StrictEnum):
    LOW_NOISE3 = "10^3 low noise"
    LOW_NOISE4 = "10^4 low noise"
    LOW_NOISE5 = "10^5 low noise"
    LOW_NOISE6 = "10^6 low noise"
    LOW_NOISE7 = "10^7 low noise"
    LOW_NOISE8 = "10^8 low noise"
    LOW_NOISE9 = "10^9 low noise"
    HIGH_SPEED5 = "10^5 high speed"
    HIGH_SPEED6 = "10^6 high speed"
    HIGH_SPEED7 = "10^7 high speed"
    HIGH_SPEED8 = "10^8 high speed"
    HIGH_SPEED9 = "10^9 high speed"
    HIGH_SPEED10 = "10^10 high spd"
    HIGH_SPEED11 = "10^11 high spd"


class QDV2F(StandardReadable):
    """
    A Quantum Detectors V2F low noise voltage to frequency converter.
    Two channel V2F - 50mHz
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        I_suffix="I",
    ) -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.intensity = epics_signal_r(float, f"{prefix}{I_suffix}")
        with self.add_children_as_readables():
            self.gain = epics_signal_rw(V2FGain, f"{prefix}GAIN")

        super().__init__(name)
