import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)

KERNAL_SIZE = (7, 7)


async def get_roi(image_arr, current_x, current_y, dist_from_x=100, dist_from_y=100):
    # need to add logic to make sure that you don't accidentally reach the end of the pixel range.
    # use the .shape method for this. this will also depend on the format of the pixel data.
    roi_arr = image_arr[
        current_y - dist_from_y : current_y + dist_from_y,
        current_x - dist_from_x : current_x + dist_from_x,
    ]

    return roi_arr


class MaxPixel(StandardReadable, Triggerable):
    """Gets the max pixel (brightest pixel) from an ROI of the beam image after some image processing."""

    def __init__(self, prefix: str, name: str = "", overlay_channel: int = 1) -> None:
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.current_centre_x = epics_signal_r(
            int, f"{prefix}OVER:{overlay_channel}:CenterX"
        ).get_value()
        self.current_centre_y = epics_signal_r(
            int, f"{prefix}OVER:{overlay_channel}:CenterY"
        ).get_value()
        self.max_pixel_val, self._max_val_setter = soft_signal_r_and_setter(float)
        super().__init__(name)

    async def _convert_to_gray_and_blur(self):
        """
        Preprocess the image array data (convert to grayscale and apply a gaussian blur)
        Image is converted to grayscale (using a weighted mean as green contributes more to brightness)
        as we aren't interested in data relating to colour. A blur is then applied to mitigate
        errors due to rogue hot pixels and provide smoother results for binarization of the image,
        which in turn gives a better ellipse fit.
        """

        data = await self.array_data.get_value()
        await get_roi(data, self.current_centre_x, self.current_centre_y)
        gray_arr = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray_arr, KERNAL_SIZE, 0)

    @AsyncStatus.wrap
    async def trigger(self):
        arr = await self.preprocessed_data()
        max_val = np.max(arr)
        assert isinstance(max_val, int)
        self._max_val_setter(max_val)
