from ophyd_async.core import HintedSignal, StandardReadable
from ophyd_async.epics.signal import epics_signal_r


class IPinAsync(StandardReadable):
    """Simple device to get the ipin reading"""

    def __init__(self, prefix: str, name: str = "") -> None:
        pin_readback = epics_signal_r(float, prefix + "I")
        self.add_readables([pin_readback], wrapper=HintedSignal)
        super().__init__(name)
