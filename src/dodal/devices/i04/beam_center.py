from typing import Any

import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)

from dodal.log import LOGGER


def binary_img(img, img_name="Threshold"):
    """
    Function which creates a binary image from a beamline image using Otsu's method for automatic thresholding.
    The threshold is increased by 10 (brightness taken from image in grayscale) in order to get more the centre of the beam.
    """
    # take this from the max pixel function preprocessing once merged in
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
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
    # use the .shape method for this
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

    def __init__(self, prefix: str, name: str = "", overlay_channel: int = 1) -> None:
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.current_centre_x = epics_signal_r(
            int, f"{prefix}OVER:{overlay_channel}:CenterX"
        ).get_value()
        self.current_centre_y = epics_signal_r(
            int, f"{prefix}OVER:{overlay_channel}:CenterY"
        ).get_value()
        self.roi_image_data = get_roi(
            self.get_img_data(), self.current_centre_x, self.current_centre_y
        )
        self.binary = binary_img(
            self.roi_image_data
        )  # does func need to be async for this and so can't go in the init?
        self.ellipse = self.fit_ellipse()
        self.center_x_val, self._center_x_val_setter = soft_signal_r_and_setter(float)
        self.center_y_val, self._center_y_val_setter = soft_signal_r_and_setter(float)
        super().__init__(name)

    async def get_img_data(self):
        return await self.array_data.get_value()

    def fit_ellipse(self):
        contours, _ = cv2.findContours(
            self.binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        if not contours:
            raise ValueError("No contours found in image.")

        largest_contour = max(contours, key=cv2.contourArea)
        if len(largest_contour) < 5:
            raise ValueError("Not enough points to fit an ellipse.")

        return cv2.fitEllipse(largest_contour)

    def center_x(self) -> Any:
        return self.ellipse[0][0]

    def center_y(self) -> Any:
        return self.ellipse[0][1]

    @AsyncStatus.wrap
    async def trigger(self):
        self._center_x_val_setter(self.center_x())
        self._center_y_val_setter(self.center_y())
