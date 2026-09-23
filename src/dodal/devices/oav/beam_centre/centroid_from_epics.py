from ophyd_async.core import (
    StandardReadable,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_rw_rbv

CC_INFIX = "CC:"
STAT_INFIX = "STAT:"


class ColourMode(StrictEnum):
    MONO = "Mono"
    BAYER = "Bayer"
    RGB1 = "RGB1"
    RGB2 = "RGB2"
    RGB3 = "RGB3"
    YUV444 = "YUV444"
    YUV422 = "YUV422"
    YUV421 = "YUV421"


class CentroidFromEpics(StandardReadable):
    """Device to set up the CAM -> CC -> STAT plugin chain and get the centroid.

    Need to spend some time thinking about taking X/Y croping on CAM into account
    """

    def __init__(
        self,
        prefix: str,
        cc_infix: str = CC_INFIX,
        stat_infix: str = STAT_INFIX,
        name: str = "",
    ):
        self.stat_array_port = epics_signal_rw_rbv(
            str, f"{prefix}{stat_infix}NDArrayPort"
        )
        self.centroid_threshold = epics_signal_rw(
            float, f"{prefix}{stat_infix}CentroidThreshold"
        )
        self.beam_centre_y = epics_signal_r(float, f"{prefix}{stat_infix}CentroidY_RBV")
        self.beam_centre_x = epics_signal_r(float, f"{prefix}{stat_infix}CentroidX_RBV")

        self.cc_array_port = epics_signal_rw_rbv(str, f"{prefix}{cc_infix}NDArrayPort")
        self.colour_mode = epics_signal_rw(
            ColourMode, f"{prefix}{cc_infix}ColorModeOut"
        )
        super().__init__(name)
