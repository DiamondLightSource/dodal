import cv2
import numpy as np
from ophyd_async.core import StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)


class MaxPixel(StandardReadable):
    """Gets the max pixel from the image"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.max_pixel_x, self._x_setter = soft_signal_r_and_setter(int)
        self.max_pixel_y, self._y_setter = soft_signal_r_and_setter(int)
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

    def _get_max_pixel_and_loc(self):
        arr = self.preprocessed_data()
        (_, max_val, _, max_loc) = cv2.minMaxLoc(arr)
        return (max_val, max_loc)

    def trigger(self):
        max_val_loc = self._get_max_pixel_and_loc()
        max_val = max_val_loc[0]  # brightest pixel value
        max_loc = max_val_loc[1]  # x, y

        self._max_val_setter(max_val)
        self._x_setter(max_loc[0])
        self._y_setter(max_loc[1])
