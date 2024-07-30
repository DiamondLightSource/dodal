from enum import Enum

import numpy as np
from numpy.typing import NDArray
from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

from dodal.devices.oav.oav_parameters import OAVConfigParams


class ZoomLevel(str, Enum):
    ONE = "1.0x"
    ONE_AND_A_HALF = "1.5x"
    TWO = "2.0x"
    TWO_AND_A_HALF = "2.5x"
    THREE = "3.0x"
    FIVE = "5.0x"
    SEVEN_AND_A_HALF = "7.5x"
    TEN = "10.0x"


class ZoomController(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.level = epics_signal_rw(ZoomLevel, prefix + "MP:SELECT")
            self.percentage = epics_signal_rw(float, prefix + "ZOOMPOSCMD")
        super().__init__(name=name)


class OAV(StandardReadable):
    def __init__(self, prefix: str, params: OAVConfigParams, name: str = "") -> None:
        self.zoom_controller = ZoomController(prefix + "-EA-OAV-01:FZOOM:")
        self.array_data = epics_signal_r(
            NDArray[np.uint8], f"pva://{prefix}-DI-OAV-01:PVA:ARRAY"
        )
        self.x_size = epics_signal_r(float, prefix + "-DI-OAV-01:MJPG:ArraySize1_RBV")
        self.y_size = epics_signal_r(float, prefix + "-DI-OAV-01:MJPG:ArraySize2_RBV")
        self.parameters = params
        self.cb = None

        super().__init__(name=name)
