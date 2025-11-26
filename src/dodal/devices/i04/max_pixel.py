import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)


class MaxPixel(StandardReadable, Triggerable):
    """Gets the max pixel from the image"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.max_pixel_val, self._max_val_setter = soft_signal_r_and_setter(float)
        super().__init__(name)

    async def preprocessed_data(self):
        """
        Preprocess the image array data (convert to grayscale and apply a guassian blur)
        """
        data = await self.array_data.get_value()
        gray_arr = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
        # kernal size describes how many of the neigbouring pixels are used for the blur,
        # higher kernal size means more of a blur effect
        kernal_size = (7, 7)
        blurred_arr = cv2.GaussianBlur(gray_arr, kernal_size, 0)
        return blurred_arr

    @AsyncStatus.wrap
    async def trigger(self):
        arr = await self.preprocessed_data()
        max_val = np.max(arr)
        self._max_val_setter(max_val)
