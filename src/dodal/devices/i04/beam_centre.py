import cv2
import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)
from scipy.optimize import curve_fit

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
    The threshold is increased by INC_BINARY_THRESH (brightness taken from image in grayscale) in order to get the inner beam.
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
    x_min = max(current_x - dist_from_x, 1)
    x_max = min(current_x + dist_from_x, width)
    y_min = max(current_y - dist_from_y, 1)
    y_max = min(current_y + dist_from_y, height)

    roi_arr = image_arr[y_min - 1 : y_max, x_min - 1 : x_max]

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
        # I am assuming that these PVs change with the zoom (need to check that this is the case)
        # Could change these so they look at the PVs for centre with zoom which look like {prefix}PBCX:VALH
        # These PVs can be found in oav_detector
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
        offset_h, overall_ssr_per_dof_h, chi_squared_per_dof_h, fit_params_h = (
            fit_ellipse_and_get_errors_for_horizontal(
                array_data, real_centre_x, real_centre_y, window=roi_dist_from_centre
            )
        )
        offset_v, overall_ssr_per_dof_v, chi_squared_per_dof_v, fit_params_v = (
            fit_ellipse_and_get_errors_for_vertical(
                array_data, real_centre_x, real_centre_y, window=roi_dist_from_centre
            )
        )
        if overall_ssr_per_dof_v < 100 and overall_ssr_per_dof_h < 100:
            self._center_x_val_setter(real_centre_x)
            self._center_y_val_setter(real_centre_y)
        else:
            LOGGER.info("Bad Guassian fit suggests centre not found!")


# errors
def gauss(x, A, mu, H, sigma):
    """
    Docstring for gauss fit
    :param A: Amplitude
    :param mu: Centre
    :param H: Vertical offset
    :param sigma: Width of peak
    """
    return (A * np.exp(-((x - mu) ** 2) / (2 * sigma**2))) + H


def fit_ellipse_and_get_errors_for_horizontal(img_array, cX, cY, window=100):  # noqa: N803
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
    if img_array is None:
        raise ValueError(f"No image data inputted")

    input_array = img_array[cY, :]
    pixel_no_h = np.arange(len(input_array))

    if window:
        start = int(max(0, cX - window))
        end = int(min(len(input_array), cX + window))

        x_fit = pixel_no_h[start:end]
        y_fit = input_array[start:end]
    else:
        x_fit = pixel_no_h
        y_fit = input_array

    # Fit Gaussian
    parameters, _ = curve_fit(
        gauss, x_fit, y_fit, p0=[max(y_fit), cX, np.min(y_fit), 5]
    )
    fit_A, fit_mu, fit_H, fit_sigma = parameters  # noqa: N806

    # Compute fitted curve
    fit_y = gauss(x_fit, fit_A, fit_mu, fit_H, fit_sigma)

    # Residuals and offset
    weight = 8
    # reciprocal of this is my estimate for the errors of the intensities of the pixel
    dof = (window * 2) - 3
    # degrees of freedom (using 3 instead of 4 to account for the extra pixel)
    residuals = y_fit - fit_y
    overall_ssr_per_dof = (
        np.sum(residuals**2) / dof
    )  # if this is greater than 150 something has gone really wrong with the fit
    residuals_with_weight = residuals * weight

    chi_squared = np.sum((residuals_with_weight) ** 2 / fit_y)
    chi_squared_per_dof = chi_squared / dof
    # chi squared close to one is a better fit
    offset = fit_mu - cX

    return (
        offset,
        overall_ssr_per_dof,
        chi_squared_per_dof,
        (fit_A, fit_mu, fit_H, fit_sigma),
    )


def fit_ellipse_and_get_errors_for_vertical(
    img_array, cX, cY, ax=None, crop=None, window=100
):
    if img_array is None:
        raise ValueError(f"No image data inputted")

    v_slice = img_array[:, cX]
    pixel_no_v = range(len(v_slice))  # Y positions

    # fit data to guassian
    start = int(max(0, cY - window))
    end = int(min(len(v_slice), cY + window))

    x_fit = pixel_no_v[start:end]
    y_fit = v_slice[start:end]

    parameters, _ = curve_fit(gauss, x_fit, y_fit, p0=[max(v_slice), cY, 10, 5])
    fit_A, fit_mu, fit_H, fit_sigma = parameters
    fit_y = gauss(x_fit, fit_A, fit_mu, fit_H, fit_sigma)

    weight = 8
    # reciprocal of this is my estimate for the errors of the intensities of the pixel
    dof = (window * 2) - 3
    # degrees of freedom (using 3 instead of 4 to account for the extra pixel)
    residuals = y_fit - fit_y
    overall_ssr_per_dof = (
        np.sum(residuals**2) / dof
    )  # if this is greater than 150 something has gone really wrong with the fit
    residuals_with_weight = residuals * weight

    chi_squared = np.sum((residuals_with_weight) ** 2 / fit_y)
    chi_squared_per_dof = chi_squared / dof
    # chi squared close to one is a better fit
    offset = fit_mu - cX

    return (
        offset,
        overall_ssr_per_dof,
        chi_squared_per_dof,
        (fit_A, fit_mu, fit_H, fit_sigma),
    )
