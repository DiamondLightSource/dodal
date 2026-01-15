import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)

from dodal.devices.oav.utils import convert_to_gray_and_blur
from dodal.log import LOGGER

# Constant was chosen from trial and error with test images
ADDITIONAL_BINARY_THRESH = 20


def convert_image_to_binary(image: np.ndarray):
    """
     Creates a binary image from OAV image array data.

    Pixels of the input image are converted to one of two values (a high and a low value).
    Otsu's method is used for automatic thresholding.
    See https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html.
    The threshold is increased by ADDITIONAL_BINARY_THRESH in order to get more of
    the centre of the beam.
    """
    max_pixel_value = 255

    blurred_image = convert_to_gray_and_blur(image)

    threshold_value, _ = cv2.threshold(
        blurred_image, 0, max_pixel_value, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Adjusting because the inner beam is less noisy compared to the outer
    threshold_value += ADDITIONAL_BINARY_THRESH

    _, thresholded_image = cv2.threshold(
        blurred_image, threshold_value, max_pixel_value, cv2.THRESH_BINARY
    )

    LOGGER.info(f"Image binarised with threshold of {threshold_value}")
    return thresholded_image


def get_roi(image_arr, current_x, current_y, dist_from_x=100, dist_from_y=100):
    # Get image dimensions
    height, width = image_arr.shape[:2]

    # Clip coordinates to stay within bounds
    x_min = max(current_x - dist_from_x, 1)
    x_max = min(current_x + dist_from_x, width)
    y_min = max(current_y - dist_from_y, 1)
    y_max = min(current_y + dist_from_y, height)

    roi_arr = image_arr[y_min - 1 : y_max, x_min - 1 : x_max]

    return roi_arr


class CentreEllipseMethod(StandardReadable, Triggerable):
    """
    Upon triggering, fits an ellipse to a binary image from the area detector defined by
    the prefix.

    This is used, in conjunction with a scintillator, to determine the centre of the beam
    on the image.
    """

    def __init__(self, prefix: str, overlay_channel: int = 1, name: str = ""):
        self.oav_array_signal = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")

        self.center_x_val, self._center_x_val_setter = soft_signal_r_and_setter(float)
        self.center_y_val, self._center_y_val_setter = soft_signal_r_and_setter(float)

        self.current_centre_x = epics_signal_r(
            int, f"{prefix}OVER:{overlay_channel}:CenterX"
        )
        self.current_centre_y = epics_signal_r(
            int, f"{prefix}OVER:{overlay_channel}:CenterY"
        )

        super().__init__(name)

    def _fit_ellipse(self, binary_img: cv2.typing.MatLike) -> cv2.typing.RotatedRect:
        contours, _ = cv2.findContours(
            binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        if not contours:
            raise ValueError("No contours found in image.")

        largest_contour = max(contours, key=cv2.contourArea)
        if len(largest_contour) < 5:
            raise ValueError(
                f"Not enough points to fit an ellipse. Found {largest_contour} points and need at least 5."
            )

        return cv2.fitEllipse(largest_contour)

    @AsyncStatus.wrap
    async def trigger(self, roi_dist_from_centre=100):
        array_data = await self.oav_array_signal.get_value()
        current_x = await self.current_centre_x.get_value()
        current_y = await self.current_centre_y.get_value()
        top_left_corner = (
            current_x - roi_dist_from_centre,
            current_y - roi_dist_from_centre,
        )
        roi_data = get_roi(
            array_data, current_x, current_y, roi_dist_from_centre, roi_dist_from_centre
        )
        binary = convert_image_to_binary(roi_data)
        ellipse_fit = self._fit_ellipse(binary)
        centre_x = ellipse_fit[0][0]
        centre_y = ellipse_fit[0][1]
        real_centre_x = centre_x + top_left_corner[0]
        real_centre_y = centre_y + top_left_corner[1]
        self._center_x_val_setter(real_centre_x)
        self._center_y_val_setter(real_centre_y)
