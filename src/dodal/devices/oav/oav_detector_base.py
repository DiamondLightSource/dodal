from enum import IntEnum

from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    LazyMock,
    SignalR,
    StandardReadable,
    derived_signal_r,
    soft_signal_rw,
)

from dodal.devices.areadetector.plugins.CAM import Cam
from dodal.devices.oav.oav_parameters import DEFAULT_OAV_WINDOW, OAVConfig
from dodal.devices.oav.snapshots.snapshot import Snapshot
from dodal.devices.oav.snapshots.snapshot_with_grid import SnapshotWithGrid

# put this into a config file
# laserOAVconfig = {
#     "microns_per_pixel_x": 6,
#     "microns_per_pixel_y": 6,
#     "beam_centre_x": 1000,
#     "beam_centre_y": 1028,
# }


class Coords(IntEnum):
    X = 0
    Y = 1


class OAVBase(StandardReadable):
    def __init__(
        self,
        prefix: str,
        config: OAVConfig,
        zoom_level: SignalR[str] | None = None,
        name: str = "",
    ):
        self.oav_config = config
        self._prefix = prefix
        self._name = name
        self.zoom_level = (
            zoom_level if zoom_level else soft_signal_rw(str, initial_value="1.0")
        )

        self.cam = Cam(f"{prefix}CAM:", name=name)

        with self.add_children_as_readables():
            self.grid_snapshot = SnapshotWithGrid(f"{prefix}MJPG:", name)
            self.sizes = [self.grid_snapshot.x_size, self.grid_snapshot.y_size]

            self.microns_per_pixel_x = derived_signal_r(
                self._get_microns_per_pixel,
                size=self.sizes[Coords.X],
                coord=soft_signal_rw(datatype=int, initial_value=Coords.X.value),
                zoom_level=self.zoom_level,
            )
            self.microns_per_pixel_y = derived_signal_r(
                self._get_microns_per_pixel,
                size=self.sizes[Coords.Y],
                coord=soft_signal_rw(datatype=int, initial_value=Coords.Y.value),
                zoom_level=self.zoom_level,
            )

            self.beam_centre_i = derived_signal_r(
                self._get_beam_position,
                size=self.sizes[Coords.X],
                coord=soft_signal_rw(datatype=int, initial_value=Coords.X.value),
                zoom_level=self.zoom_level,
            )
            self.beam_centre_j = derived_signal_r(
                self._get_beam_position,
                size=self.sizes[Coords.Y],
                coord=soft_signal_rw(datatype=int, initial_value=Coords.Y.value),
                zoom_level=self.zoom_level,
            )

            self.snapshot = Snapshot(
                f"{self._prefix}MJPG:",
                self._name,
            )

        super().__init__(name)

    def _get_microns_per_pixel(self, size: int, coord: int, zoom_level: str) -> float:
        """Extracts the microns per x pixel and y pixel for a given zoom level."""
        _zoom = zoom_level
        value = self.parameters[_zoom].microns_per_pixel[coord]
        return value * DEFAULT_OAV_WINDOW[coord] / size

    def _get_beam_position(self, size: int, coord: int, zoom_level: str) -> int:
        """Extracts the beam location in pixels `xCentre` `yCentre`, for a requested \
        zoom level. """
        _zoom = zoom_level
        value = self.parameters[_zoom].crosshair[coord]

        return int(value * size / DEFAULT_OAV_WINDOW[coord])

    async def connect(
        self,
        mock: bool | LazyMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ):
        self.parameters = self.oav_config.get_parameters()

        return await super().connect(mock, timeout, force_reconnect)
