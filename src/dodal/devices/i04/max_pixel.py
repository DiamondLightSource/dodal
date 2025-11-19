import cv2
import numpy as np
from ophyd_async.core import (
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_r


class MaxPixel(StandardReadable):
    """Gets the max pixel from the image"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        # type: ignore
        pass

    def preprocess(self):
        gray_arr = cv2.cvtColor(self.array_data, cv2.COLOR_BGR2GRAY)  # type: ignore
        blurred_arr = cv2.GaussianBlur(gray_arr, (7, 7), 0)
        return blurred_arr

    def _get_max_pixel_and_loc(self):
        # convert to grayscale
        arr = self.preprocess()
        (_, max_val, _, max_loc) = cv2.minMaxLoc(arr)
        return (max_val, max_loc)
