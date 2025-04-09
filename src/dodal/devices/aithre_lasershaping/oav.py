from enum import IntEnum
from functools import partial

from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    LazyMock,
    StandardReadable,
    derived_signal_r,
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


class OAV(StandardReadable):
    def __init__(self, prefix: str, config: OAVConfig, name: str = ""):
        self.oav_config = config
        self._prefix = prefix
        self._name = name

        self.cam = Cam(f"{prefix}CAM:", name=name)

        with self.add_children_as_readables():
            self.grid_snapshot = SnapshotWithGrid(f"{prefix}MJPG:", name)
            self.microns_per_pixel_x = derived_signal_r(
                lambda: self._get_microns_per_pixel(axis=Coords.X)
            )
            self.microns_per_pixel_x = derived_signal_r(
                lambda: self._get_microns_per_pixel(axis=Coords.Y)
            )

            self.beam_centre_i = derived_signal_r(
                partial(self._get_beam_position, axis=Coords.X),
                size=self.grid_snapshot.x_size,
            )
            self.beam_centre_j = derived_signal_r(
                partial(self._get_beam_position, axis=Coords.Y),
                size=self.grid_snapshot.y_size,
            )

            self.snapshot = Snapshot(
                f"{self._prefix}MJPG:",
                self._name,
            )

        self.sizes = [self.grid_snapshot.x_size, self.grid_snapshot.y_size]

        super().__init__(name)

    def _get_beam_position(self, axis, size) -> int:
        """Extracts the beam location in pixels `xCentre` `yCentre`"""
        value = self.parameters["1.0"].crosshair[axis]
        return int(value * size / DEFAULT_OAV_WINDOW[axis])

    def _get_microns_per_pixel(self, axis: IntEnum) -> float:
        return self.parameters["1.0"].microns_per_pixel[axis]

    async def connect(
        self,
        mock: bool | LazyMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ):
        self.parameters = self.oav_config.get_parameters()

        return await super().connect(mock, timeout, force_reconnect)
