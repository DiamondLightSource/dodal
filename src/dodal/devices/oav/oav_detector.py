from enum import IntEnum

from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    LazyMock,
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.common.signal_utils import create_r_hardware_backed_soft_signal
from dodal.devices.aithre_lasershaping.oav import OAV
from dodal.devices.areadetector.plugins.CAM import Cam
from dodal.devices.oav.oav_parameters import DEFAULT_OAV_WINDOW, OAVConfig
from dodal.devices.oav.snapshots.snapshot import Snapshot
from dodal.devices.oav.snapshots.snapshot_with_grid import SnapshotWithGrid


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
    you should wait on any zoom changs to finish before changing the OAV wiring.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.percentage = epics_signal_rw(float, f"{prefix}ZOOMPOSCMD")

        # Level is the string description of the zoom level e.g. "1.0x" or "1.0"
        self.level = epics_signal_rw(str, f"{prefix}MP:SELECT")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: str):
        await self.level.set(value, wait=True)


class OAVWithZoom(OAV):
    def __init__(self, prefix: str, config: OAVConfig, name: str = ""):
        _bl_prefix = prefix.split("-")[0]
        self.zoom_controller = ZoomController(f"{_bl_prefix}-EA-OAV-01:FZOOM:", name)

        super().__init__(name, config)

    def _read_current_zoom(self, _zoom: str) -> str:
        return _get_correct_zoom_string(_zoom)

    def _get_microns_per_pixel(
        self, size: int, coord: int, zoom_level: str = "1.0"
    ) -> float:
        """Extracts the microns per x pixel and y pixel for a given zoom level."""
        _zoom = self._read_current_zoom(zoom_level)
        value = self.parameters[_zoom].microns_per_pixel[coord]
        return value * DEFAULT_OAV_WINDOW[coord] / size

    def _get_beam_position(self, size: int, coord: int, zoom_level: str = "1.0") -> int:
        """Extracts the beam location in pixels `xCentre` `yCentre`, for a requested \
        zoom level. """
        _zoom = self._read_current_zoom(zoom_level)
        value = self.parameters[_zoom].crosshair[coord]

        return int(value * size / DEFAULT_OAV_WINDOW[coord])
