from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_rw


class Scatterguard(StandardReadable):
    """The scatterguard device."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = epics_signal_rw(float, prefix + "X")
        self.y = epics_signal_rw(float, prefix + "Y")
        super().__init__(name)
