import asyncio

from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    PathProvider,
    SignalR,
    StandardReadable,
)
from ophyd_async.epics.adaravis import AravisController, AravisDetector
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

from dodal.common.signal_utils import create_hardware_backed_soft_signal


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
    async def allowed_zoom_levels(self):
        return asyncio.gather(
            *[level.get_value() for level in list(self.all_levels.values())]
        )

    @AsyncStatus.wrap
    async def set(self, level_to_set: str):
        await self.level.set(level_to_set, wait=True)


# NOTE: Would a common base to be used by oav and NXsasOAV make sense/be useful???
class OAV(AravisDetector):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix: str,
        hdf_suffix: str,
        params,
        name: str = "",
        gpio_number: AravisController.GPIO_NUMBER = 1,
    ):
        super().__init__(
            prefix, path_provider, drv_suffix, hdf_suffix, name, gpio_number
        )

        self.zoom_controller = ZoomController(prefix, name)
        self.parameters = params

        # Just an example, need to do the same for all of them
        self.micronsPerXPixel = create_hardware_backed_soft_signal(
            int, self._get_microns_per_pixel
        )

    async def _get_microns_per_pixel(self):
        pass
