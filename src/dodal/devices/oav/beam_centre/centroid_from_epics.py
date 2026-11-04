import asyncio

from bluesky.protocols import Preparable, Stageable
from ophyd_async.core import (
    AsyncStatus,
    EnableDisable,
    StandardReadable,
    StrictEnum,
)
from ophyd_async.epics.adcore import NDStatsIO
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_rw_rbv
from pydantic import BaseModel

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


class CentroidSettings(BaseModel):
    threshold: float
    colour_mode: ColourMode


class CentroidFromEpics(StandardReadable, Preparable, Stageable):
    """Device to set up the CAM -> CC -> STAT plugin chain and get the centroid.

    The CC plugin is used to set the colour mode (Mono for black and white).
    The STAT plugin is used to calculate the centroid and threshold needs to be set to
    eliminate noise.
    Note that the STAT plugin may be disabled on some beamlines so it needs to be
    switched on.
    """

    def __init__(
        self,
        prefix: str,
        cc_infix: str = CC_INFIX,
        stat_infix: str = STAT_INFIX,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.cam_port_name = epics_signal_r(str, f"{prefix}CAM:PortName_RBV")
            self.cc_port_name = epics_signal_r(str, f"{prefix}{CC_INFIX}PortName_RBV")
            self.cc_array_port = epics_signal_rw_rbv(
                str, f"{prefix}{cc_infix}NDArrayPort"
            )
            self.colour_mode = epics_signal_rw(
                ColourMode, f"{prefix}{cc_infix}ColorModeOut"
            )
            self.stats = NDStatsIO(prefix=f"{prefix}{STAT_INFIX}")
            self.beam_centre_x = epics_signal_r(
                float, f"{prefix}{stat_infix}CentroidX_RBV"
            )
            self.beam_centre_y = epics_signal_r(
                float, f"{prefix}{stat_infix}CentroidY_RBV"
            )
        super().__init__(name)

    @AsyncStatus.wrap
    async def prepare(self, value: CentroidSettings):
        """Prepare the camera to read the centroid by setting up the plugin chain."""
        _cam_port_name = await self.cam_port_name.get_value()
        _cc_port_name = await self.cc_port_name.get_value()
        await asyncio.gather(
            self.cc_array_port.set(_cam_port_name),
            self.colour_mode.set(value.colour_mode),
            self.stats.nd_array_port.set(_cc_port_name),
            self.stats.centroid_threshold.set(value.threshold),
        )

    @AsyncStatus.wrap
    async def stage(self):
        """Once the device is prepared, switch on the stats plugin.

        This is done by enabling the callback and setting the ComputeCentroid and
        ComputeStatistics PVs to YES.
        (Note that Histogram and Profiles may be needed as well, needs testing.)

        This step may be needed as keeping this plugin always running uses a lot of CPU,
        thus the beamline may have switched it off.
        """
        await asyncio.gather(
            self.stats.enable_callbacks.set(EnableDisable.ENABLE),
            self.stats.compute_statistics.set(True),
            self.stats.compute_centroid.set(True),
            # NOTE To test if actually necessary
            self.stats.compute_profiles.set(True),
            self.stats.compute_histogram.set(True),
        )

    @AsyncStatus.wrap
    async def unstage(self):
        """Switch the stats plugin back off once done."""
        await asyncio.gather(
            self.stats.enable_callbacks.set(EnableDisable.DISABLE),
            self.stats.compute_statistics.set(False),
            self.stats.compute_centroid.set(False),
            # NOTE To test if actually necessary
            self.stats.compute_profiles.set(False),
            self.stats.compute_histogram.set(False),
        )
