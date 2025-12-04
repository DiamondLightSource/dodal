from collections.abc import AsyncGenerator
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import cv2
import numpy as np
import pytest
from ophyd_async.core import init_devices

from dodal.devices.i04.max_pixel import KERNAL_SIZE, MaxPixel, convert_to_gray_and_blur


@pytest.fixture
async def max_pixel() -> AsyncGenerator[MaxPixel]:
    async with init_devices(mock=True):
        max_pixel = MaxPixel("TEST: MAX_PIXEL")
    yield max_pixel


@pytest.mark.parametrize(
    "preprocessed_data, expected",
    [
        ([1, 2, 3], 3),  # test can handle standard input
        ([[0, 0, 0], [0, 0, 0], [0, 0, 0]], 0),  # test can handle all 0's
        ([-9, -8, 0], 0),  # test can handle negatives
        ([6.9, 8.9, 7.5, 6.45], 8.9),  # check can handle floats
    ],
)
@patch("dodal.devices.i04.max_pixel.convert_to_gray_and_blur")
async def test_returns_max(
    mocked_preprocessed_data: AsyncMock,
    preprocessed_data,
    expected,
    max_pixel: MaxPixel,
):
    mocked_preprocessed_data.return_value = preprocessed_data
    await max_pixel.trigger()
    assert await max_pixel.max_pixel_val.get_value() == expected


@patch("dodal.devices.i04.max_pixel.cv2.cvtColor")
@patch("dodal.devices.i04.max_pixel.cv2.GaussianBlur")
async def test_preprocessed_data_grayscale_is_called(
    mocked_cv2_blur: MagicMock,
    mocked_cv2_grey: MagicMock,
):
    data = np.array([1])
    convert_to_gray_and_blur(data)
    mocked_cv2_grey.assert_called_once_with(data, cv2.COLOR_BGR2GRAY)
    mocked_cv2_blur.assert_called_once_with(ANY, KERNAL_SIZE, 0)


test_arr = np.array(
    [
        [[123, 65, 0], [0, 0, 0], [0, 0, 0]],
        [[123, 65, 0], [0, 0, 0], [0, 0, 0]],
        [[123, 65, 0], [0, 0, 0], [0, 0, 0]],
        [[123, 65, 0], [0, 0, 0], [0, 0, 0]],
    ],
    dtype=np.uint8,
)


async def test_greyscale_works():
    test_arr_shape = test_arr.shape  # (4, 3, 3)
    processed_data = convert_to_gray_and_blur(test_arr)
    processed_data_shape = processed_data.shape  # (4,3)

    assert processed_data_shape[0] == test_arr_shape[0]
    assert processed_data_shape[1] == test_arr_shape[1]
