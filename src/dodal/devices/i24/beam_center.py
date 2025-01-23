"""A small temporary device to get the beam center positions from \
    eiger or pilatus detector on i24"""

from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw


class DetectorBeamCenter(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.beam_x = epics_signal_rw(float, prefix + "BeamX")  # in pixels
        self.beam_y = epics_signal_rw(float, prefix + "BeamY")
        super().__init__(name)
