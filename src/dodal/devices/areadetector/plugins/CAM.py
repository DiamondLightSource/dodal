from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class ColorMode(StrictEnum):
    """
    Enum to store the various color modes of the camera. We use RGB1.
    """

    MONO = "Mono"
    BAYER = "Bayer"
    RGB1 = "RGB1"
    RGB2 = "RGB2"
    RGB3 = "RGB3"
    YUV444 = "YUV444"
    YUV422 = "YUV422"
    YUV421 = "YUV421"


class Cam(StandardReadable):
    """
    Camera device class for area detector plugins.

    This class represents a camera interface with standard readable properties,
    providing access to common camera controls and status signals via EPICS.

    Args:
        prefix (str): The EPICS PV prefix for the camera.
        name (str, optional): The name of the camera device. Defaults to "".

    Attributes:
        color_mode: Read/write EPICS signal for the camera's color mode.
        acquire_period: Read/write EPICS signal for the acquisition period (float).
        acquire_time: Read/write EPICS signal for the acquisition time (float).
        gain: Read/write EPICS signal for the camera gain (float).
        array_size_x: Read-only EPICS signal for the X dimension of the image array (int).
        array_size_y: Read-only EPICS signal for the Y dimension of the image array (int).
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.color_mode = epics_signal_rw(ColorMode, prefix + "ColorMode")
        self.acquire_period = epics_signal_rw(float, prefix + "AcquirePeriod")
        self.acquire_time = epics_signal_rw(float, prefix + "AcquireTime")
        self.gain = epics_signal_rw(float, prefix + "Gain")

        self.array_size_x = epics_signal_r(int, prefix + "ArraySizeX_RBV")
        self.array_size_y = epics_signal_r(int, prefix + "ArraySizeY_RBV")
        super().__init__(name)
