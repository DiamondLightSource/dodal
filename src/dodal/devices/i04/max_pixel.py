import cv2
import numpy as np
from ophyd_async.core import StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)


class MaxPixel(StandardReadable):
    """Gets the max pixel from the image"""

    def __init__(self, prefix: str, name: str = "", overlay_channel: int = 1) -> None:
        self.array_data = epics_signal_r(
            np.ndarray, prefix + f"pva://{prefix}PVA:ARRAY"
        )
        self.current_centre_x = epics_signal_r(
            int, prefix + f"OVER:{overlay_channel}:CenterX"
        )
        self.current_centre_y = epics_signal_r(
            int, prefix + f"OVER:{overlay_channel}:CenterY"
        )
        self.dist_from_x = 100
        self.dist_from_y = 100
        self.max_pixel_x, self._x_setter = soft_signal_r_and_setter(int)
        self.max_pixel_y, self._y_setter = soft_signal_r_and_setter(int)
        self.max_pixel_val, self._max_val_setter = soft_signal_r_and_setter(float)

    async def get_roi(
        self, arr, dist_from_x: int | None = None, dist_from_y: int | None = None
    ):
        """This gets an ROI and crops the image based on where the previous centre was"""
        if dist_from_x is None:
            dist_from_x = self.dist_from_x
        if dist_from_y is None:
            dist_from_y = self.dist_from_y

        x = await self.current_centre_x.get_value()
        y = await self.current_centre_y.get_value()

        roi = arr[y : y + dist_from_y, x : x + dist_from_x]

        # update the class variables so that you can revert the coords back to full image after.
        self.dist_from_y = dist_from_y
        self.dist_from_x = dist_from_x

        return roi

    # all i need is the centre and the top left corner coords which I can calculate from the distance I input.

    def preprocessed_data(
        self, dist_from_x: int | None = None, dist_from_y: int | None = None
    ):
        """
        Preprocess the image array data (convert to grayscale and apply a guassian blur)
        """
        arr_data = self.array_data.get_value()
        roi_data = self.get_roi(arr_data, dist_from_x, dist_from_y)
        gray_arr = cv2.cvtColor(roi_data, cv2.COLOR_BGR2GRAY)  # type: ignore
        blurred_arr = cv2.GaussianBlur(gray_arr, (7, 7), 0)
        return blurred_arr

    def _get_max_pixel_and_loc(self):
        arr = self.preprocessed_data()
        (_, max_val, _, max_loc) = cv2.minMaxLoc(arr)
        return (max_val, max_loc)

    async def _convert_coords_to_image_coords(self):
        # this function will convert back to image coords.
        # the max pixel on the roi image
        max_loc_cropped = self._get_max_pixel_and_loc()[1]

        current_x = await self.current_centre_x.get_value()
        current_y = await self.current_centre_y.get_value()

        # you  just add whatever the top left coords are to get the actual from the cropped
        top_left_x, top_left_y = (
            current_x - self.dist_from_x,
            current_y - self.dist_from_y,
        )
        # the actual max_pixel
        max_loc_x = max_loc_cropped[0] + top_left_x
        max_loc_y = max_loc_cropped[1] + top_left_y

        return max_loc_x, max_loc_y

    def trigger(self):
        max_val_loc = self._get_max_pixel_and_loc()
        max_val = max_val_loc[0]
        max_loc = max_val_loc[1]

        self._max_val_setter(max_val)
        self._x_setter(max_loc[0])
        self._y_setter(max_loc[1])
