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
    Function which creates a binary image from a beamline image using Otsu's method for automatic threshholding.
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


class CentreEllipseMethod(StandardReadable, Triggerable):
    def __init__(self, prefix: str, name: str = ""):
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.binary = binary_img(
            self.get_img_data()
        )  # does func need to be async for this
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
