from ophyd_async.core import StandardReadable, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r


class IPin(StandardReadable):
    """Simple device to get the ipin reading"""

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(
            format=StandardReadableFormat.HINTED_SIGNAL
        ):
            self.pin_readback = epics_signal_r(float, prefix + "I")
        super().__init__(name)
