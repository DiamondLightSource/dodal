from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# import cv2
import numpy as np
import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i04.max_pixel import MaxPixel


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


def test_preprocessed_data_grayscale(mock_array, max_pixel: MaxPixel):
    arr = np.array(
        [
            [[200, 100, 150], [200, 200, 200], [300, 150, 200]],
            [[200, 100, 150], [200, 200, 200], [300, 150, 200]],
            [[200, 100, 150], [200, 200, 200], [300, 150, 200]],
        ]
    )
    arr_shape = arr.shape  # (i, j, 3)
    set_mock_value(max_pixel.array_data, arr)
    blurred = max_pixel.preprocessed_data()
    assert isinstance(blurred, np.ndarray)
    assert blurred.shape == (arr_shape[0], arr_shape[1])
    # assert blurred.shape == mock_array.shape
