import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)

# kernal size describes how many of the neigbouring pixels are used for the blur,
# higher kernal size means more of a blur effect
KERNAL_SIZE = (7, 7)


class MaxPixel(StandardReadable, Triggerable):
    """Gets the max pixel (brightest pixel) from the image after some image processing."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.max_pixel_val, self._max_val_setter = soft_signal_r_and_setter(float)
        super().__init__(name)

    async def _convert_to_gray_and_blur(self):
        """
        Preprocess the image array data (convert to grayscale and apply a gaussian blur)
        Image is converted to grayscale (using a weighted mean as green contributes more to brightness)
        as we aren't interested in data relating to colour. A blur is then applied to mitigate
        errors due to rogue hot pixels.
        """
        data = await self.array_data.get_value()
        gray_arr = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray_arr, KERNAL_SIZE, 0)

    @AsyncStatus.wrap
    async def trigger(self):
        arr = await self._convert_to_gray_and_blur()
        max_val = float(np.max(arr))  # np.int64
        assert isinstance(max_val, float)
        self._max_val_setter(max_val)
