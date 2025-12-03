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


from scipy.optimize import curve_fit


# to get vertical do array_data[:, cX]
# to get horizonAL do array_data[cY, :]
# need to call with cX for horizontal slice and cY for vertical slice
def gauss(x, A, mu, H, sigma):
    return (A * np.exp(-((x - mu) ** 2) / (2 * sigma**2))) + H


# h_slice = img[cY, :]
import numpy as np
from scipy.optimize import curve_fit


def gauss(x, A, mu, H, sigma):
    return (A * np.exp(-((x - mu) ** 2) / (2 * sigma**2))) + H


def fit_ellipse_and_get_errors_for_horizontal(input_array, cX, cY, window=50):
    """
    Fit a Gaussian to a horizontal slice of the image and return
    the center offset and residuals.

    Parameters:
        input_array (np.ndarray): 1D horizontal slice of the image.
        cX (int): X-coordinate of the center.
        cY (int): Y-coordinate of the center (used for offset).
        window (int): Half-width of fitting window around cX.

    Returns:
        offset (float): Difference between fitted mean and cY.
        residuals (np.ndarray): y_fit - fitted_y for the chosen window.
        fit_params (tuple): (A, mu, H, sigma) from the fit.
    """
    pixel_no_h = np.arange(len(input_array))

    # Define fitting window
    start = int(max(0, cX - window))
    end = int(min(len(input_array), cX + window))

    x_fit = pixel_no_h[start:end]
    y_fit = input_array[start:end]

    # Fit Gaussian
    parameters, _ = curve_fit(
        gauss, x_fit, y_fit, p0=[max(y_fit), cX, np.min(y_fit), 5]
    )
    fit_A, fit_mu, fit_H, fit_sigma = parameters

    # Compute fitted curve
    fit_y = gauss(x_fit, fit_A, fit_mu, fit_H, fit_sigma)

    # Residuals
    residuals = y_fit - fit_y
    overall_ssr = np.sum(residuals**2)

    # Offset from expected center
    offset = fit_mu - cY

    return offset, overall_ssr
