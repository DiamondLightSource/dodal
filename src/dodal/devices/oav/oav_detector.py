from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    derived_signal_r,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.oav.oav_detector_base import OAVBase
from dodal.devices.oav.oav_parameters import OAVConfig


# Workaround to deal with the fact that beamlines may have slightly different string
# descriptions of the zoom level"
def _get_correct_zoom_string(zoom: str) -> str:
    if zoom.endswith("x"):
        zoom = zoom.strip("x")
    return zoom


class ZoomController(StandardReadable, Movable[str]):
    """
    Device to control the zoom level. This should be set like
        o = OAV(name="oav")
        oav.zoom_controller.set("1.0x")

    Note that changing the zoom may change the AD wiring on the associated OAV, as such
    you should wait on any zoom changes to finish before changing the OAV wiring.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.percentage = epics_signal_rw(float, f"{prefix}ZOOMPOSCMD")

        # Level is the string description of the zoom level e.g. "1.0x" or "1.0"
        self.level = epics_signal_rw(str, f"{prefix}MP:SELECT")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: str):
        await self.level.set(value, wait=True)


class OAV(OAVBase):
    def __init__(self, prefix: str, config: OAVConfig, name: str = ""):
        _bl_prefix = prefix.split("-")[0]
        self.zoom_controller = ZoomController(f"{_bl_prefix}-EA-OAV-01:FZOOM:", name)

        self.zoom_level = derived_signal_r(
            self._get_zoom_level, zoom_level=self.zoom_controller.level
        )

        super().__init__(
            prefix=prefix,
            config=config,
            name=name,
            zoom_level=self.zoom_level,
        )

    def _get_zoom_level(self, zoom_level: str) -> str:
        return _get_correct_zoom_string(zoom_level)
