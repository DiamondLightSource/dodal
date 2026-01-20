from unittest.mock import ANY, MagicMock, call, patch

import cv2
import numpy as np
import pytest
from ophyd_async.core import init_devices, set_mock_value

from dodal.devices.i04.beam_centre import (
    CentreEllipseMethod,
    convert_image_to_binary,
    get_roi,
)


@pytest.fixture
async def centre_device() -> CentreEllipseMethod:
    async with init_devices(mock=True):
        centre_device = CentreEllipseMethod("TEST: ELLIPSE_CENTRE")
    dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
    set_mock_value(centre_device.oav_array_signal, dummy_img)
    return centre_device


@pytest.fixture
def test_image_array():
    return np.array(
        [
            [00, 10, 20, 30, 40],
            [1, 11, 21, 31, 41],
            [2, 12, 22, 32, 24],
            [3, 13, 23, 33, 43],
            [4, 14, 24, 34, 44],
        ],
        dtype=np.uint8,
    )


@patch("dodal.devices.i04.beam_centre.cv2.threshold")
@patch("dodal.devices.i04.beam_centre.convert_to_gray_and_blur")
async def test_convert_image_to_binary_calls_threshold_twice(
    mock_convert, mock_threshold
):
    fake_img = np.ones((10, 10), dtype=np.uint8) * 127
    mock_threshold.return_value = (127, fake_img)
    mock_convert.return_value = fake_img

    convert_image_to_binary(fake_img)

    mock_convert.assert_called_once()

    assert mock_threshold.call_count == 2

    # check the args from the two times it's called.
    first_call_args = mock_threshold.call_args_list[0][0]
    second_call_args = mock_threshold.call_args_list[1][0]

    # First call should use Otsu
    assert first_call_args[3] == cv2.THRESH_BINARY + cv2.THRESH_OTSU
    # Second call should use the adjusted threshold
    assert second_call_args[1] == 147


@patch("dodal.devices.i04.beam_centre.cv2.findContours")
@patch("dodal.devices.i04.beam_centre.cv2.fitEllipse")
async def test_fit_ellipse_good_params(
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

    await centre_device.trigger()
    fit_ellipse.assert_called_once()


async def test_fit_ellipse_raises_error_if_not_enough_image_points(
    centre_device: CentreEllipseMethod,
):
    with pytest.raises(ValueError, match="No contours found in image."):
        await centre_device.trigger()


@pytest.mark.parametrize(
    "mock_contours",
    [
        [np.array([[[0, 0]], [[1, 0]], [[1, 1]]])],  # 3 points (triangle)
        [
            np.array([[[10, 10]], [[20, 10]], [[20, 20]], [[10, 20]]])
        ],  # 4 points (square)
    ],
)
@patch("dodal.devices.i04.beam_centre.cv2.findContours")
async def test_fit_ellipse_raises_error_if_not_enough_contour_points(
    find_contours_mock: MagicMock,
    centre_device: CentreEllipseMethod,
    mock_contours: np.ndarray,
):
    hierarchy = np.array([[[-1, -1, -1, -1]]])
    find_contours_mock.return_value = (mock_contours, hierarchy)

    with pytest.raises(ValueError, match="Not enough points to fit an ellipse."):
        await centre_device.trigger()


@patch("dodal.devices.i04.beam_centre.CentreEllipseMethod._fit_ellipse")
@patch("dodal.devices.i04.beam_centre.convert_image_to_binary")
async def test_trigger_converts_to_binary_then_finds_ellipse(
    mock_convert_to_binary: MagicMock,
    mock_fit_ellipse: MagicMock,
    centre_device: CentreEllipseMethod,
):
    parent_mock = MagicMock()
    parent_mock.attach_mock(mock_convert_to_binary, "convert_to_binary")
    parent_mock.attach_mock(mock_fit_ellipse, "fit_ellipse")

    await centre_device.trigger()

    mock_convert_to_binary.assert_called_once()
    mock_fit_ellipse.assert_called_once()

    assert parent_mock.mock_calls.index(
        call.convert_to_binary(ANY)
    ) < parent_mock.mock_calls.index(call.fit_ellipse(ANY))


async def test_real_image_gives_expected_centre(
    centre_device: CentreEllipseMethod,
):
    image = cv2.imread("tests/test_data/scintillator_with_beam.jpg")
    assert image is not None
    image = np.asarray(image[:, :])
    set_mock_value(centre_device.oav_array_signal, image)
    set_mock_value(centre_device.roi_box_size, 10000)
    await centre_device.trigger()

    assert await centre_device.center_x_val.get_value() == pytest.approx(727.8381)
    assert await centre_device.center_y_val.get_value() == pytest.approx(365.4453)


@pytest.mark.parametrize(
    "centre_xy, box_dimensions, expected",
    [
        ((2, 2), (3, 3), [[11, 21, 31], [12, 22, 32], [13, 23, 33]]),
        (
            (3, 3),
            (20, 100),
            [
                [00, 10, 20, 30, 40],
                [1, 11, 21, 31, 41],
                [2, 12, 22, 32, 24],
                [3, 13, 23, 33, 43],
                [4, 14, 24, 34, 44],
            ],
        ),
        ((2, 2), (4, 2), [[1, 11, 21, 31], [2, 12, 22, 32]]),
        ((1, 1), (3, 1), [[1, 11, 21]]),
        ((1, 4), (1, 3), [[13], [14]]),
        ((4, 4), (5, 5), [[22, 32, 24], [23, 33, 43], [24, 34, 44]]),
    ],
)
def test_get_roi_creates_correct_image_array(
    test_image_array: np.ndarray,
    centre_xy: tuple[int, int],
    box_dimensions: tuple[int, int],
    expected: list[list[int]],
):
    result, _, _ = get_roi(
        image_arr=test_image_array,
        centre_x=centre_xy[0],
        centre_y=centre_xy[1],
        box_width=box_dimensions[0],
        box_height=box_dimensions[1],
    )
    assert (result == expected).all()


def test_get_roi_creates_box_with_correct_shape():
    test_image_array = np.zeros((500, 500))
    result, _, _ = get_roi(
        image_arr=test_image_array,
        centre_x=200,
        centre_y=200,
        box_width=150,
        box_height=250,
    )
    assert result.shape == (250, 150)  # (height, width)


async def test_real_image_gives_expected_centre_with_roi(
    centre_device: CentreEllipseMethod,
):
    image = cv2.imread("tests/test_data/scintillator_with_beam.jpg")
    assert image is not None
    image = np.asarray(image[:, :])
    set_mock_value(centre_device.oav_array_signal, image)
    set_mock_value(centre_device.current_centre_x, 700)
    set_mock_value(centre_device.current_centre_y, 400)
    set_mock_value(centre_device.roi_box_size, 300)

    await centre_device.trigger()

    assert await centre_device.center_x_val.get_value() == pytest.approx(727.8, abs=0.1)
    assert await centre_device.center_y_val.get_value() == pytest.approx(365.4, abs=0.1)
