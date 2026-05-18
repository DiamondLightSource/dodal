from ophyd_async.core import (
    StandardReadable,
    StandardReadableFormat,
)
from ophyd_async.epics.core import epics_signal_r


class Flux(StandardReadable):
    """i02-1 currently don't have a PV for the flux at the sample position. for now, XBPM3 flux is sufficient
    for reading and sending the flux to ispyb during gridscans.
    """

    def __init__(self, prefix: str, name="") -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.flux_reading = epics_signal_r(float, prefix + "XBPM-03")
            super().__init__(name=name)
