from enum import IntEnum

from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

from dodal.common.signal_utils import create_hardware_backed_soft_signal
from dodal.devices.oav.oav_parameters import DEFAULT_OAV_WINDOW, OAVConfig
from dodal.devices.oav.snapshots.snapshot_with_beam_centre import SnapshotWithBeamCentre


class Coords(IntEnum):
    X = 0
    Y = 1


# Workaround to deal with the fact that beamlines may have slightly different string
# descriptions of the zoom level"
def _get_correct_zoom_string(zoom: str) -> str:
    if zoom.endswith("x"):
        zoom = zoom.strip("x")
    return zoom


class ZoomController(StandardReadable):
    """
    Device to control the zoom level. This should be set like
        o = OAV(name="oav")
        oav.zoom_controller.set("1.0x")

    Note that changing the zoom may change the AD wiring on the associated OAV, as such
    you should wait on any zoom changs to finish before changing the OAV wiring.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(name=name)
        self.percentage = epics_signal_rw(float, f"{prefix}ZOOMPOSCMD")

        # Level is the string description of the zoom level e.g. "1.0x" or "1.0"
        self.level = epics_signal_rw(str, f"{prefix}MP:SELECT")

    @AsyncStatus.wrap
    async def set(self, level_to_set: str):
        await self.level.set(level_to_set, wait=True)


class OAV(StandardReadable):
    def __init__(self, prefix: str, config: OAVConfig, name: str = ""):
        self.snapshot = SnapshotWithBeamCentre(f"{prefix}-DI-OAV-01:MJPG:", name)
        _bl_prefix = prefix.split("-")[0]
        self.zoom_controller = ZoomController(f"{_bl_prefix}-EA-OAV-01:FZOOM:", name)

        # TODO See https://github.com/DiamondLightSource/dodal/issues/824
        self.x_size = epics_signal_r(int, prefix + "CAM:ArraySizeX_RBV")
        self.y_size = epics_signal_r(int, prefix + "CAM:ArraySizeY_RBV")

        self.sizes = [self.x_size, self.y_size]

        self.parameters = config.get_parameters()

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

        self._set_up_snapshot()

        super().__init__(name)

    def _set_up_snapshot(self):
        self.snapshot.microns_per_pixel_x = self.microns_per_pixel_x
        self.snapshot.microns_per_pixel_y = self.microns_per_pixel_y
        self.snapshot.beam_centre_i = self.beam_centre_i
        self.snapshot.beam_centre_j = self.beam_centre_j

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

    async def calculate_beam_distance(
        self, horizontal_pixels: int, vertical_pixels: int
    ) -> tuple[int, int]:
        """
        Calculates the distance between the beam centre and the given (horizontal, vertical).

        Args:
            horizontal_pixels (int): The x (camera coordinates) value in pixels.
            vertical_pixels (int): The y (camera coordinates) value in pixels.
        Returns:
            The distance between the beam centre and the (horizontal, vertical) point in pixels as a tuple
            (horizontal_distance, vertical_distance).
        """
        beam_x = await self.beam_centre_i.get_value()
        beam_y = await self.beam_centre_j.get_value()

        return (
            beam_x - horizontal_pixels,
            beam_y - vertical_pixels,
        )
