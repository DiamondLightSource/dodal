import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)

from dodal.devices.i04.max_pixel import convert_to_gray_and_blur
from dodal.log import LOGGER

# constant was chosen from trial and error with test images
INC_BINARY_THRESH = 20


def binary_img(img, img_name="Threshold"):
    """
     Creates a binary image from OAV image array data.

    Pixels of the input image are converted to one of two values (a high and a low value).
    Otsu's method is used for automatic thresholding.
    See https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html.
    The threshold is increased by [constant name] (brightness taken from image in grayscale)
    in order to get more of the centre of the beam.
    """
    # convert to greyscale as not interested in information relating to colour and blur to eliminate rouge hot pixels
    blurred = convert_to_gray_and_blur(img)
    assert blurred is not None, "Image is None before thresholding"

    (thresh, thresh_img) = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    # adjusting because the inner beam is less noisy compared to the outer.
    thresh += INC_BINARY_THRESH

    thresh_img = cv2.threshold(blurred, thresh, 255, cv2.THRESH_BINARY)[1]

    LOGGER.info(f"Thresholding value (otsu with blur): {thresh}")
    return thresh_img


def get_roi(image_arr, current_x, current_y, dist_from_x=100, dist_from_y=100):
    # Get image dimensions
    height, width = image_arr.shape[:2]

    # Clip coordinates to stay within bounds
    x_min = max(current_x - dist_from_x, 0)
    x_max = min(current_x + dist_from_x, width)
    y_min = max(current_y - dist_from_y, 0)
    y_max = min(current_y + dist_from_y, height)

    roi_arr = image_arr[y_min:y_max, x_min:x_max]

    return roi_arr


class CentreEllipseMethod(StandardReadable, Triggerable):
    """
    Fits an ellipse a binary image of the beam. The centre of the fitted ellipse is taken
    to be the centre of the beam.
    Centre is found through fitting an ellipse and extracting the centre.
    First a ROI is taken which is taken at 100 pixels from the PVs for the previous centre.
    Then the image is converted to a binary (see above function), after which an ellipse is
    fitted.
    The placeholder PVs for the centre are then updated.
    """

    def __init__(self, prefix: str, name: str = "", overlay_channel: int = 1):
        self.array_signal = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.center_x_val, self._center_x_val_setter = soft_signal_r_and_setter(float)
        self.center_y_val, self._center_y_val_setter = soft_signal_r_and_setter(float)
        self.current_centre_x = epics_signal_r(
            int, f"{prefix}OVER:{overlay_channel}:CenterX"
        )
        self.current_centre_y = epics_signal_r(
            int, f"{prefix}OVER:{overlay_channel}:CenterY"
        )
        super().__init__(name)

    def fit_ellipse(self, binary_img: cv2.typing.MatLike) -> cv2.typing.RotatedRect:
        contours, _ = cv2.findContours(
            binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        if not contours:
            raise ValueError("No contours found in image.")

        largest_contour = max(contours, key=cv2.contourArea)
        if len(largest_contour) < 5:
            raise ValueError("Not enough points to fit an ellipse.")

        return cv2.fitEllipse(largest_contour)

    @AsyncStatus.wrap
    async def trigger(self, roi_dist_from_centre=100):
        array_data = await self.array_signal.get_value()
        current_x = await self.current_centre_x.get_value()
        current_y = await self.current_centre_y.get_value()
        top_left_corner = (
            current_x - roi_dist_from_centre,
            current_y - roi_dist_from_centre,
        )
        roi_data = get_roi(
            array_data, current_x, current_y, roi_dist_from_centre, roi_dist_from_centre
        )
        binary = binary_img(roi_data)
        ellipse_fit = self.fit_ellipse(binary)
        centre_x = ellipse_fit[0][0]
        centre_y = ellipse_fit[0][1]
        # convert back to original image coords
        real_centre_x = centre_x + top_left_corner[0]
        real_centre_y = centre_y + top_left_corner[1]
        self._center_x_val_setter(real_centre_x)
        self._center_y_val_setter(real_centre_y)
