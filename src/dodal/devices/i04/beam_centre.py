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


class CentreEllipseMethod(StandardReadable, Triggerable):
    """
    Fits an ellipse a binary image of the beam. The centre of the fitted ellipse is taken
    to be the centre of the beam.
    """

    def __init__(self, prefix: str, name: str = ""):
        self.array_signal = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")

        self.center_x_val, self._center_x_val_setter = soft_signal_r_and_setter(float)
        self.center_y_val, self._center_y_val_setter = soft_signal_r_and_setter(float)
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
    async def trigger(self):
        array_data = await self.array_signal.get_value()
        binary = await binary_img(array_data)
        ellipse_fit = self.fit_ellipse(binary)
        centre_x = ellipse_fit[0][0]
        centre_y = ellipse_fit[0][1]
        self._center_x_val_setter(centre_x)
        self._center_y_val_setter(centre_y)
