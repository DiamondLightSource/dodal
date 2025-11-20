import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)


class MaxPixel(StandardReadable, Triggerable):
    """Gets the max pixel from the image"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.max_pixel_val, self._max_val_setter = soft_signal_r_and_setter(float)

    def preprocessed_data(
        self, dist_from_x: int | None = None, dist_from_y: int | None = None
    ):
        """
        Preprocess the image array data (convert to grayscale and apply a guassian blur)
        """
        gray_arr = cv2.cvtColor(self.array_data, cv2.COLOR_BGR2GRAY)  # type: ignore
        blurred_arr = cv2.GaussianBlur(gray_arr, (7, 7), 0)
        return blurred_arr

    def trigger(self):
        arr = self.preprocessed_data()
        max_val = np.max(arr)
        self._max_val_setter(max_val)
