from enum import IntEnum

from ophyd_async.core import DEFAULT_TIMEOUT, AsyncStatus, LazyMock, StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.common.signal_utils import create_hardware_backed_soft_signal
from dodal.devices.areadetector.plugins.CAM import Cam
from dodal.devices.oav.oav_parameters import DEFAULT_OAV_WINDOW, OAVConfig
from dodal.devices.oav.snapshots.snapshot_with_beam_centre import SnapshotWithBeamCentre
from dodal.devices.oav.snapshots.snapshot_with_grid import SnapshotWithGrid
from dodal.log import LOGGER

# put this into a config file
laserOAVconfig = {"microns_per_pixel_x": 6,
                  "microns_per_pixel_y": 6,
                  "beam_centre_x": 1000,
                  "beam_centre_y": 1028,
                }

class OAV(StandardReadable)
    def __init__(self, prefix: str, config: OAVConfig, name: str = ""):
        self.oav_config = config
        self._prefix = prefix
        self._name =  name
        _bl_prefix = prefix.split("-")[0]
        # don't need zoom controller

        self.cam = Cam(f"{prefix}CAM:", name=name)

        with self.add_children_as_readables():
            self.grid_snapshot = SnapshotWithGrid(f"{prefix}MJPG:", name)
            self.microns_per_pixel_x = laserOAVconfig["microns_per_pixel_x"]
            self.microns_per_pixel_y = laserOAVconfig["microns_per_pixel_y"]
            self.beam_centre_x = create_hardware_backed_soft_signal(int, lambda: self._get_beam_position("X"))
            self.beam_centre_y = create_hardware_backed_soft_signal(int, lambda: self._get_beam_position("Y"))
            self.snapshot = SnapshotWithBeamCentre(
                f"{self._prefix}MJPG:",
                self.beam_centre_x,
                self.beam_centre_y,
                self._name,
            )

        self.sizes = [self.grid_snapshot.x_size, self.grid_snapshot.y_size]

        super().__init__(name)

    async def _get_beam_position(self, coord: str) -> int:
        if coord == "X":
            value = laserOAVconfig["beam_centre_x"]
        elif coord == "Y":
            value = laserOAVconfig["beam_centre_y"]
        else:
            LOGGER.error("NO AXIS DEFINED FOR BEAM POSITION")
            value = 1
        return value


# LA18L-DI-OAV-01: is prefix for lab 18 OAV laser shaping
# not sure if I need to use this or just create a new json and use the standard
