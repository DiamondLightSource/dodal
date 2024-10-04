from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    PathProvider,
    SignalR,
    StandardReadable,
)
from ophyd_async.core._utils import DEFAULT_TIMEOUT
from ophyd_async.epics.adaravis import AravisController, AravisDetector
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

from dodal.common.signal_utils import create_hardware_backed_soft_signal
from dodal.devices.oav.oav_utils import OAVConfig

# GDA currently assumes this aspect ratio for the OAV window size.
# For some beamline this doesn't affect anything as the actual OAV aspect ratio
# matches. Others need to take it into account to rescale the values stored in
# the configuration files.
DEFAULT_OAV_WINDOW = (1024, 768)


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
        self.percentage = epics_signal_rw(float, "ZOOMPOSCMD")

        # Level is the string description of the zoom level e.g. "1.0x" or "1.0"
        self.level = epics_signal_rw(str, f"{prefix}MP:SELECT")

        self.all_levels: DeviceVector[SignalR[str]] = DeviceVector(
            {
                "zrst": epics_signal_r(str, f"{prefix}MP:SELECT.ZRST"),
                "onst": epics_signal_r(str, f"{prefix}MP:SELECT.ONST"),
                "twst": epics_signal_r(str, f"{prefix}MP:SELECT.TWST"),
                "thst": epics_signal_r(str, f"{prefix}MP:SELECT.THST"),
                "frst": epics_signal_r(str, f"{prefix}MP:SELECT.FRST"),
                "fvst": epics_signal_r(str, f"{prefix}MP:SELECT.FVST"),
                "sxst": epics_signal_r(str, f"{prefix}MP:SELECT.SXST"),
            }
        )

    @property
    async def allowed_zoom_levels(self) -> list[str]:
        res = [await level.get_value() for level in list(self.all_levels.values())]
        return res

    @AsyncStatus.wrap
    async def set(self, level_to_set: str):
        await self.level.set(level_to_set, wait=True)


class OAV(AravisDetector):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix: str,
        hdf_suffix: str,
        config: OAVConfig,
        name: str = "",
        gpio_number: AravisController.GPIO_NUMBER = 1,
    ):
        super().__init__(
            prefix, path_provider, drv_suffix, hdf_suffix, name, gpio_number
        )

        self.zoom_controller = ZoomController(prefix, name)
        # TODO This will actually come from the MJPG but for now...
        self.x_size = epics_signal_r(int, prefix + "CAM:ArraySizeX_RBV")
        self.y_size = epics_signal_r(int, prefix + "CAM:ArraySizeY_RBV")

        self.parameters = config.get_parameters()

    async def _read_current_zoom(self) -> str:
        _zoom = await self.zoom_controller.level.get_value()
        return _get_correct_zoom_string(_zoom)

    async def _get_microns_per_pixel(self, coord: str) -> float:
        _zoom = await self._read_current_zoom()
        match coord:
            case "x":
                value = self.parameters[_zoom].microns_per_pixel_x
                x_size = await self.x_size.get_value()
                return value * DEFAULT_OAV_WINDOW[0] / x_size
            case "y":
                value = self.parameters[_zoom].microns_per_pixel_y
                y_size = await self.x_size.get_value()
                return value * DEFAULT_OAV_WINDOW[1] / y_size

    async def _get_beam_position(self, coord: str) -> int:
        _zoom = await self._read_current_zoom()
        match coord:
            case "x":
                value = self.parameters[_zoom].crosshair_x
                x_size = await self.x_size.get_value()
                return int(value * x_size / DEFAULT_OAV_WINDOW[0])
            case "y":
                value = self.parameters[_zoom].crosshair_y
                y_size = await self.y_size.get_value()
                return int(value * y_size / DEFAULT_OAV_WINDOW[1])

    async def connect(
        self,
        mock: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ):
        self.micronsPerXPixel = create_hardware_backed_soft_signal(
            float,
            lambda: self._get_microns_per_pixel("x"),
        )
        self.micronsPerYPixel = create_hardware_backed_soft_signal(
            float,
            lambda: self._get_microns_per_pixel("y"),
        )

        self.beam_centre_i = create_hardware_backed_soft_signal(
            int, lambda: self._get_beam_position("x")
        )

        self.beam_centre_j = create_hardware_backed_soft_signal(
            int, lambda: self._get_beam_position("y")
        )

        return await super().connect(mock, timeout, force_reconnect)
