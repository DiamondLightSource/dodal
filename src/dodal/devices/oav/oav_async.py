from ophyd_async.core import (
    AsyncStatus,
    PathProvider,
    StandardReadable,
)
from ophyd_async.epics.adaravis import AravisController, AravisDetector
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

from dodal.common.signal_utils import create_hardware_backed_soft_signal
from dodal.devices.oav.oav_parameters import DEFAULT_OAV_WINDOW, OAVConfig


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


class OAV(AravisDetector):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        config: OAVConfig,
        drv_suffix: str = "CAM:",
        hdf_suffix: str = "HDF5:",
        name: str = "",
        gpio_number: AravisController.GPIO_NUMBER = 1,
    ):
        super().__init__(
            prefix, path_provider, drv_suffix, hdf_suffix, name, gpio_number
        )

        _bl_prefix = prefix.split("-")[0]
        self.zoom_controller = ZoomController(f"{_bl_prefix}-EA-OAV-01:FZOOM:", name)

        # TODO See https://github.com/DiamondLightSource/dodal/issues/824
        self.x_size = epics_signal_r(int, prefix + "CAM:ArraySizeX_RBV")
        self.y_size = epics_signal_r(int, prefix + "CAM:ArraySizeY_RBV")

        self.parameters = config.get_parameters()

        self.microns_per_pixel_x = create_hardware_backed_soft_signal(
            float,
            lambda: self._get_microns_per_pixel("x"),
        )
        self.microns_per_pixel_y = create_hardware_backed_soft_signal(
            float,
            lambda: self._get_microns_per_pixel("y"),
        )

        self.beam_centre_i = create_hardware_backed_soft_signal(
            int, lambda: self._get_beam_position("x")
        )

        self.beam_centre_j = create_hardware_backed_soft_signal(
            int, lambda: self._get_beam_position("y")
        )

    async def _read_current_zoom(self) -> str:
        _zoom = await self.zoom_controller.level.get_value()
        return _get_correct_zoom_string(_zoom)

    async def _get_microns_per_pixel(self, coord: str) -> float:  # type: ignore
        """Extracts the microns per x pixel and y pixel for a given zoom level."""
        _zoom = await self._read_current_zoom()
        if coord == "x":
            value = self.parameters[_zoom].microns_per_pixel_x
            x_size = await self.x_size.get_value()
            return value * DEFAULT_OAV_WINDOW[0] / x_size
        if coord == "y":
            value = self.parameters[_zoom].microns_per_pixel_y
            y_size = await self.y_size.get_value()
            return value * DEFAULT_OAV_WINDOW[1] / y_size

    async def _get_beam_position(self, coord: str) -> int:  # type: ignore
        """Extracts the beam location in pixels `xCentre` `yCentre`, for a requested zoom \
        level. """
        _zoom = await self._read_current_zoom()
        if coord == "x":
            value = self.parameters[_zoom].crosshair_x
            x_size = await self.x_size.get_value()
            return int(value * x_size / DEFAULT_OAV_WINDOW[0])
        if coord == "y":
            value = self.parameters[_zoom].crosshair_y
            y_size = await self.y_size.get_value()
            return int(value * y_size / DEFAULT_OAV_WINDOW[1])

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
