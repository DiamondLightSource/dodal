import math

import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.epics.core import (
    epics_signal_r,
)

from dodal.devices.oav.utils import convert_to_gray_and_blur
from dodal.log import LOGGER

# Constant was chosen from trial and error with test images
ADDITIONAL_BINARY_THRESH = 20


def convert_image_to_binary(image: np.ndarray):
    """Creates a binary image from OAV image array data.

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


def round_half_up(x):
    return int(math.floor(x + 0.5))


def get_roi(
    image_arr: np.ndarray,
    centre_x: int,
    centre_y: int,
    box_width: int = 200,
    box_height: int = 200,
) -> tuple[np.ndarray, tuple[int, int], tuple[int, int]]:
    """Creates an ROI image array from a full screen image array, given a centre for the
    ROI image and a width and height of the ROI box. Note that if the centre of the ROI
    box is close to the edge of the full screen image, the box may be smaller than the
    width and height provided, as the ROI will be trimmed to fit inside the full screen
    image.

    Args:
        image_arr (np.ndarray): The full screen image array.
        centre_x (int): The x coordinate of the centre of the ROI box.
        centre_y (int): The y coordinate of the centre of the ROI box.
        box_width (int, optional): The width of the ROI box. Defaults to 200.
        box_height (int, optional): The height of the ROI box. Defaults to 200.

    Returns:
        tuple[np.ndarray, tuple[int, int], tuple[int, int]]: The ROI array, and (x, y)
            coordinates of the top left and bottom right corners of the ROI box.
    """
    height, width = image_arr.shape[:2]
    x_dist = (box_width) / 2
    y_dist = (box_height) / 2

    # Clip coordinates to stay within bounds
    x_min = max(round_half_up(centre_x - x_dist), 0)
    x_max = min(round_half_up(centre_x + x_dist), width) - 1
    y_min = max(round_half_up(centre_y - y_dist), 0)
    y_max = min(round_half_up(centre_y + y_dist), height) - 1

    roi_arr = image_arr[y_min : y_max + 1, x_min : x_max + 1]

    return roi_arr, (x_min, y_min), (x_max, y_max)


class CentreEllipseMethod(StandardReadable, Triggerable):
    """Upon triggering, fits an ellipse to a binary image from the area detector defined
    by the prefix.

    This is used, in conjunction with a scintillator, to determine the centre of the
    beam on the image.
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

        self.roi_box_size = soft_signal_rw(int, 300)

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
    async def trigger(self):
        array_data = await self.oav_array_signal.get_value()
        current_x = await self.current_centre_x.get_value()
        current_y = await self.current_centre_y.get_value()
        roi_box_size = await self.roi_box_size.get_value()

        roi_data, top_left_corner, _ = get_roi(
            array_data, current_x, current_y, roi_box_size, roi_box_size
        )

        roi_binary = convert_image_to_binary(roi_data)
        ellipse_fit = self._fit_ellipse(roi_binary)
        roi_centre_x = ellipse_fit[0][0]
        roi_centre_y = ellipse_fit[0][1]
        # convert back to full screen image coords and set beam centre
        self._center_x_val_setter(roi_centre_x + top_left_corner[0])
        self._center_y_val_setter(roi_centre_y + top_left_corner[1])
