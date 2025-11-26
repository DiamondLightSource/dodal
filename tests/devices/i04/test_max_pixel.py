from collections.abc import AsyncGenerator
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch

# import cv2
import cv2
import numpy as np
import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i04.max_pixel import KERNAL_SIZE, MaxPixel


@pytest.fixture
async def max_pixel() -> AsyncGenerator[MaxPixel]:
    async with init_devices(mock=True):
        max_pixel = MaxPixel("TEST: MAX_PIXEL")
    yield max_pixel


@pytest.mark.parametrize(
    "arr_m, expected",
    [([1, 2, 3], 3), ([[0, 0, 0], [0, 0, 0], [0, 0, 0]], 0), ([-9, -8, 0], 0)],
)
@patch("dodal.devices.i04.max_pixel.MaxPixel.preprocessed_data")
async def test_returns_max(
    mocked_preprocessed_data: AsyncMock, arr_m, expected, max_pixel: MaxPixel
):
    # set_mock_value(max_pixel.array_data, arr) -> should test that the preprocessed bit works
    mocked_preprocessed_data.return_value = arr_m
    await max_pixel.trigger()
    assert await max_pixel.max_pixel_val.get_value() == expected


@patch("dodal.devices.i04.max_pixel.cv2.cvtColor")
@patch("dodal.devices.i04.max_pixel.cv2.GaussianBlur")
async def test_preprocessed_data_grayscale(
    mocked_cv2_blur: MagicMock, mocked_cv2_grey: MagicMock, max_pixel: MaxPixel
):
    data = np.array([1])
    set_mock_value(max_pixel.array_data, data)
    await max_pixel.preprocessed_data()
    mocked_cv2_grey.assert_called_once_with(data, cv2.COLOR_BGR2GRAY)
    mocked_cv2_blur.assert_called_once_with(ANY, KERNAL_SIZE, 0)
