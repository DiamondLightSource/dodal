from ophyd_async.core import (
    StandardReadable,
)
from ophyd_async.epics.core import (
    epics_signal_r,
)


class CentroidFromEpics(StandardReadable):
    """
    Needs plugn chain CAM -> CC( to make B/W) -> STAT.

    Need to spend some time thinking about taking X/Y croping on CAM into account
    """

    def __init__(self, prefix: str, name: str = ""):
        self.beam_centre_y = epics_signal_r(float, "BL19I-EA-OAV-01:STAT:CentroidY_RBV")
        self.beam_centre_x = epics_signal_r(float, "BL19I-EA-OAV-01:STAT:CentroidX_RBV")
        super().__init__(name)
