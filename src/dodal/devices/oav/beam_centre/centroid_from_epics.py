import asyncio

from bluesky.protocols import Preparable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_rw_rbv
from pydantic import BaseModel

CC_INFIX = "CC:"
STAT_INFIX = "STAT:"

CAM_PLUGIN_NAME = "OAV1.cam"
CC_PLUGIN_NAME = "OAV1.cc"


class ColourMode(StrictEnum):
    MONO = "Mono"
    BAYER = "Bayer"
    RGB1 = "RGB1"
    RGB2 = "RGB2"
    RGB3 = "RGB3"
    YUV444 = "YUV444"
    YUV422 = "YUV422"
    YUV421 = "YUV421"


# NOTE will also need to make a triggerable to start it up (all the enables etc)
class CentroidSettings(BaseModel):
    threshold: float
    colour_mode: ColourMode


class CentroidFromEpics(StandardReadable, Preparable):
    """Device to set up the CAM -> CC -> STAT plugin chain and get the centroid."""

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
        self.cc_array_port = epics_signal_rw_rbv(str, f"{prefix}{cc_infix}NDArrayPort")
        with self.add_children_as_readables():
            self.centroid_threshold = epics_signal_rw(
                float, f"{prefix}{stat_infix}CentroidThreshold"
            )
            self.beam_centre_y = epics_signal_r(
                float, f"{prefix}{stat_infix}CentroidY_RBV"
            )
            self.beam_centre_x = epics_signal_r(
                float, f"{prefix}{stat_infix}CentroidX_RBV"
            )
            self.colour_mode = epics_signal_rw(
                ColourMode, f"{prefix}{cc_infix}ColorModeOut"
            )
        super().__init__(name)

    @AsyncStatus.wrap
    async def prepare(self, value: CentroidSettings):
        """Prepare the camera to read the centroid by setting up the plugin chain."""
        await asyncio.gather(
            self.cc_array_port.set(CAM_PLUGIN_NAME),
            self.colour_mode.set(value.colour_mode),
            self.stat_array_port.set(CC_PLUGIN_NAME),
            self.centroid_threshold.set(value.threshold),
        )
