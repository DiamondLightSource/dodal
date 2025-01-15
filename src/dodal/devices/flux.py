from ophyd_async.core import (
    StandardReadable,
    StandardReadableFormat,
)
from ophyd_async.epics.core import epics_signal_r


class Flux(StandardReadable):
    """Simple device to get the flux reading"""

    def __init__(self, prefix: str, name="") -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.flux_reading = epics_signal_r(float, prefix + "SAMP")
            super().__init__(name=name)
