from enum import IntEnum

from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    LazyMock,
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.signal_utils import create_hardware_backed_soft_signal
from dodal.devices.areadetector.plugins.CAM import Cam
from dodal.devices.oav.oav_parameters import (
    DEFAULT_OAV_WINDOW,
    OAVConfig,
    OAVConfigNoBeamCentre,
)
from dodal.devices.oav.snapshots.snapshot_with_beam_centre import SnapshotWithBeamCentre
from dodal.devices.oav.snapshots.snapshot_with_grid import SnapshotWithGrid


class Coords(IntEnum):
    X = 0
    Y = 1


# Workaround to deal with the fact that beamlines may have slightly different string
# descriptions of the zoom level"
def _get_correct_zoom_string(zoom: str) -> str:
    if zoom.endswith("x"):
        zoom = zoom.strip("x")
    return zoom


class ZoomController(StandardReadable, Movable):
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


class OAV(StandardReadable):
    def __init__(self, prefix: str, config: OAVConfig, name: str = ""):
        self.oav_config = config
        self._prefix = prefix
        self._name = name
        _bl_prefix = prefix.split("-")[0]
        self.zoom_controller = ZoomController(f"{_bl_prefix}-EA-OAV-01:FZOOM:", name)

        self.cam = Cam(f"{prefix}CAM:", name=name)

        with self.add_children_as_readables():
            self.grid_snapshot = SnapshotWithGrid(f"{prefix}MJPG:", name)
            self.microns_per_pixel_x = create_hardware_backed_soft_signal(
                float,
                lambda: self._get_microns_per_pixel(Coords.X),
            )
            self.microns_per_pixel_y = create_hardware_backed_soft_signal(
                float,
                lambda: self._get_microns_per_pixel(Coords.Y),
            )
            self.beam_centre_i = create_hardware_backed_soft_signal(
                int, lambda: self._get_beam_position(Coords.X)
            )
            self.beam_centre_j = create_hardware_backed_soft_signal(
                int, lambda: self._get_beam_position(Coords.Y)
            )
            self.snapshot = SnapshotWithBeamCentre(
                f"{self._prefix}MJPG:",
                self.beam_centre_i,
                self.beam_centre_j,
                self._name,
            )

        self.sizes = [self.grid_snapshot.x_size, self.grid_snapshot.y_size]

        super().__init__(name)

    async def _read_current_zoom(self) -> str:
        _zoom = await self.zoom_controller.level.get_value()
        return _get_correct_zoom_string(_zoom)

    async def _get_microns_per_pixel(self, coord: int) -> float:
        """Extracts the microns per x pixel and y pixel for a given zoom level."""
        _zoom = await self._read_current_zoom()
        value = self.parameters[_zoom].microns_per_pixel[coord]
        size = await self.sizes[coord].get_value()
        return value * DEFAULT_OAV_WINDOW[coord] / size

    async def _get_beam_position(self, coord: int) -> int:
        """Extracts the beam location in pixels `xCentre` `yCentre`, for a requested \
        zoom level. """
        _zoom = await self._read_current_zoom()
        value = self.parameters[_zoom].crosshair[coord]
        size = await self.sizes[coord].get_value()
        return int(value * size / DEFAULT_OAV_WINDOW[coord])

    async def connect(
        self,
        mock: bool | LazyMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ):
        self.parameters = self.oav_config.get_parameters()

        return await super().connect(mock, timeout, force_reconnect)


class OAVBeamCentre(OAV):
    def __init__(
        self, prefix: str, config: OAVConfigNoBeamCentre, name: str = "", roi=True
    ):
        beam_centre_roi_x = epics_signal_r(int, prefix + "OVER:1:CenterX")
        beam_centre_roi_y = epics_signal_r(int, prefix + "OVER:1:CenterY")
        beam_centre_fs_x = epics_signal_r(int, prefix + "OVER:3:CenterX")
        beam_centre_fs_y = epics_signal_r(int, prefix + "OVER:3:CenterY")
        if roi:
            self.beam_centre_x = beam_centre_roi_x
            self.beam_centre_y = beam_centre_roi_y
        else:
            self.beam_centre_x = beam_centre_fs_x
            self.beam_centre_y = beam_centre_fs_y
        super().__init__(prefix, config, name)

    async def _get_beam_position(self, coord: int) -> int:
        """Extracts the beam location in pixels `xCentre` `yCentre`."""
        value = await (self.beam_centre_x, self.beam_centre_y)[coord].get_value()
        size = await self.sizes[coord].get_value()
        return int(value * size / DEFAULT_OAV_WINDOW[coord])
