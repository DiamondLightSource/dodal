from collections.abc import AsyncGenerator
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from ophyd_async.core import init_devices

from dodal.devices.i04.beam_centre import CentreEllipseMethod, binary_img, get_roi


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

    binary_img(fake_img)
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


@patch("dodal.devices.i04.beam_centre.CentreEllipseMethod.fit_ellipse")
@patch("dodal.devices.i04.beam_centre.binary_img")
@patch("dodal.devices.i04.beam_centre.get_roi")
async def test_trigger(
    mock_roi_img: MagicMock,
    mock_binary_img: MagicMock,
    mock_fit_ellipse: MagicMock,
    centre_device: CentreEllipseMethod,
):
    await centre_device.trigger()
    mock_roi_img.assert_called_once()
    mock_binary_img.assert_called_once()
    mock_fit_ellipse.assert_called_once()


test_img = np.array(
    [
        [0, 0, 0, 0, 0],
        [0, 5, 5, 5, 0],
        [0, 5, 10, 5, 0],
        [0, 5, 5, 5, 0],
        [0, 0, 0, 0, 0],
    ],
    dtype=np.uint8,
)


def test_roi_logic():
    # checking test img
    assert test_img.shape == (5, 5)
    assert test_img[2, 2] == 10

    # test previous centre in middle
    expected_result = [[5, 5, 5], [5, 10, 5], [5, 5, 5]]
    standard_test = get_roi(
        image_arr=test_img, current_x=3, current_y=3, dist_from_x=1, dist_from_y=1
    )
    assert (standard_test == expected_result).all()

    # test when you go out of bounds for the roi
    out_of_bounds = get_roi(
        image_arr=test_img, current_x=3, current_y=3, dist_from_x=10, dist_from_y=50
    )
    assert (out_of_bounds == test_img).all()

    # test different dist from x and dist from y
    diff_x_and_y = get_roi(
        image_arr=test_img, current_x=3, current_y=3, dist_from_x=2, dist_from_y=1
    )
    print(diff_x_and_y)
    expected_result = [[0, 5, 5, 5, 0], [0, 5, 10, 5, 0], [0, 5, 5, 5, 0]]
    assert (diff_x_and_y == expected_result).all()

    # test when previous centre is not in middle
    off_centre = get_roi(
        image_arr=test_img, current_x=2, current_y=3, dist_from_x=2, dist_from_y=1
    )
    expected_result = [[0, 5, 5, 5], [0, 5, 10, 5], [0, 5, 5, 5]]
    assert (off_centre == expected_result).all()

    # test another off centre and part out of bounds
    off_centre_2 = get_roi(
        image_arr=test_img, current_x=2, current_y=2, dist_from_x=2, dist_from_y=2
    )
    expected_result = [
        [0, 0, 0, 0],
        [0, 5, 5, 5],
        [0, 5, 10, 5],
        [0, 5, 5, 5],
    ]
    assert (off_centre_2 == expected_result).all()
