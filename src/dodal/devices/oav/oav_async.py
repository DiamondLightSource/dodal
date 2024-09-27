from ophyd_async.core import PathProvider, StandardReadable
from ophyd_async.epics.adaravis import AravisController, AravisDetector
from ophyd_async.epics.signal import epics_signal_rw


class ZoomController(StandardReadable):
    """
    Device to control the zoom level. This should be set like
        o = OAV(name="oav")
        oav.zoom_controller.set("1.0x")

    Note that changing the zoom may change the AD wiring on the associated OAV, as such
    you should wait on any zoom changs to finish before changing the OAV wiring.
    """

    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self.percentage = epics_signal_rw(float, "ZOOMPOSCMD")
        # Level is the string description of the zoom level e.g. "1.0x" or "1.0"
        self.level = epics_signal_rw(str, "MP:SELECT")


class OAV(AravisDetector):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix: str,
        hdf_suffix: str,
        name: str = "",
        gpio_number: AravisController.GPIO_NUMBER = 1,
    ):
        super().__init__(
            prefix, path_provider, drv_suffix, hdf_suffix, name, gpio_number
        )
