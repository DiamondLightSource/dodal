from collections.abc import AsyncGenerator
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from ophyd_async.core import init_devices

from dodal.devices.i04.beam_centre import CentreEllipseMethod, binary_img


@pytest.fixture
async def centre_device() -> AsyncGenerator[CentreEllipseMethod]:
    async with init_devices(mock=True):
        centre_device = CentreEllipseMethod("TEST: ELLIPSE_CENTRE")
    yield centre_device


@patch("dodal.devices.i04.beam_centre.cv2.threshold")
@patch("dodal.devices.i04.beam_centre.convert_to_gray_and_blur")
async def test_binary_img_calls_threshold_twice(mock_convert, mock_threshold):
    fake_img = np.ones((10, 10), dtype=np.uint8) * 127
    mock_threshold.return_value = (127, fake_img)
    mock_convert.return_value = fake_img

    await binary_img(fake_img)
    assert mock_threshold.call_count == 2

    # check the args from the two times it's called.
    first_call_args = mock_threshold.call_args_list[0][0]
    second_call_args = mock_threshold.call_args_list[1][0]

    # First call should use Otsu
    assert first_call_args[3] == cv2.THRESH_BINARY + cv2.THRESH_OTSU
    # Second call should use the adjusted threshold
    assert second_call_args[1] == 147


contour_array = np.array(
    [[[10, 10]], [[10, 50]], [[50, 50]], [[50, 10]]], dtype=np.uint8
)


@patch("dodal.devices.i04.beam_centre.cv2.findContours")
@patch("dodal.devices.i04.beam_centre.cv2.fitEllipse")
def test_fit_ellipse_good_params(
    fit_ellipse: MagicMock,
    find_contours_mock: MagicMock,
    centre_device: CentreEllipseMethod,
):
    contours = [
        np.array(
            [[[10, 20]], [[15, 25]], [[20, 30]], [[25, 25]], [[30, 20]], [[20, 15]]]
        )
    ]
    hierarchy = np.array([[[-1, -1, -1, -1]]])
    find_contours_mock.return_value = (contours, hierarchy)
    dummy_img = np.zeros((10, 10), dtype=np.uint8)

    centre_device.fit_ellipse(dummy_img)
    fit_ellipse.assert_called_once()


@patch("dodal.devices.i04.beam_centre.cv2.findContours")
async def test_fit_ellipse_raises_error_if_not_enough_image_points(
    find_contours_mock: MagicMock, centre_device: CentreEllipseMethod
):
    find_contours_mock.return_value = (None, None)
    dummy_img = np.zeros((10, 10), dtype=np.uint8)

    with pytest.raises(ValueError, match="No contours found in image."):
        centre_device.fit_ellipse(dummy_img)


@patch("dodal.devices.i04.beam_centre.cv2.findContours")
def test_fit_ellipse_raises_error_if_not_enough_contour_points(
    find_contours_mock: MagicMock, centre_device: CentreEllipseMethod
):
    contours = [
        np.array([[[0, 0]], [[1, 0]], [[1, 1]]]),  # 3 points (triangle)
        np.array([[[10, 10]], [[20, 10]], [[20, 20]], [[10, 20]]]),  # 4 points (square)
    ]

    hierarchy = np.array([[[-1, -1, -1, -1], [-1, -1, -1, -1]]])
    find_contours_mock.return_value = (contours, hierarchy)
    dummy_img = np.zeros((10, 10), dtype=np.uint8)

    with pytest.raises(ValueError, match="Not enough points to fit an ellipse."):
        centre_device.fit_ellipse(dummy_img)
