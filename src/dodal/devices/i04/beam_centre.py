import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)

from dodal.devices.i04.max_pixel import convert_to_gray_and_blur
from dodal.log import LOGGER


async def binary_img(img, img_name="Threshold"):
    """
    Function which creates a binary image from a beamline image. This is where the
    pixels of an image are converted to one of two values (a high and a low value).
    Otsu's method is used for automatic threshholding.
    See https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html.
    The threshold is increased by 10 (brightness taken from image in grayscale)
    in order to get more the centre of the beam.
    """
    blurred = await convert_to_gray_and_blur(img)
    assert blurred is not None, "Image is None before thresholding"
    print(blurred.shape, blurred.dtype)

    (thresh, thresh_img) = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    # adjusting because the inner beam is less noisy compared to the outer.
    thresh += 20

    thresh_img = cv2.threshold(blurred, thresh, 255, cv2.THRESH_BINARY)[1]

    LOGGER.info(f"[INFO] thresholding value (otsu with blur): {thresh}")
    return thresh_img


async def get_roi(image_arr, current_x, current_y, dist_from_x=100, dist_from_y=100):
    # need to add logic to make sure that you don't accidentally reach the end of the pixel range.
    # use the .shape method for this. this will also depend on the format of the pixel data.
    roi_arr = image_arr[
        current_y - dist_from_y : current_y + dist_from_y,
        current_x - dist_from_x : current_x + dist_from_x,
    ]

    return roi_arr


class CentreEllipseMethod(StandardReadable, Triggerable):
    """
    Finds the centre of the beam through fitting an ellipse and extracting the centre.
    First a ROI is taken which is taken at 100 pixels from the PVs for the previous centre.
    Then the image is converted to a binary (see above function), after which an ellipse is
    fitted.
    The placeholder PVs should then be updated (but not sure if that is happening yet).
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

    def fit_ellipse(self, binary_img):
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
        roi_data = await get_roi(
            array_data, current_x, current_y, roi_dist_from_centre, roi_dist_from_centre
        )
        binary = await binary_img(roi_data)
        ellipse_fit = self.fit_ellipse(binary)
        centre_x = ellipse_fit[0][0]
        centre_y = ellipse_fit[0][1]
        # convert back to original image coords
        real_centre_x = centre_x + top_left_corner[0]
        real_centre_y = centre_y + top_left_corner[1]
        self._center_x_val_setter(real_centre_x)
        self._center_y_val_setter(real_centre_y)
