from collections.abc import AsyncGenerator
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import git
import numpy as np
import pytest
from cv2 import threshold
from ophyd_async.core import init_devices, set_mock_value

from dodal.devices.i04.beam_centre import CentreEllipseMethod, binary_img


@pytest.fixture
async def beam_centre_ellipse() -> AsyncGenerator[CentreEllipseMethod]:
    async with init_devices(mock=True):
        max_pixel = CentreEllipseMethod("TEST: ELLIPSE_CENTRE")
    yield max_pixel


test_arr = np.array(
    [
        [[123, 100, 100], [0, 0, 0], [0, 0, 0]],
        [[123, 100, 100], [0, 0, 0], [0, 0, 0]],
        [[123, 100, 100], [0, 0, 0], [0, 0, 0]],
        [[123, 100, 100], [0, 0, 0], [0, 0, 0]],
    ],
    dtype=np.uint8,
)

expected_result = np.array(
    [[255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0]],
    dtype=np.uint8,
)


@patch("dodal.devices.i04.beam_centre.cv2.threshold")
async def test_binary_img(mock_threshold_func: MagicMock):
    await binary_img(test_arr)  # maybe you need to use real image data for this to work
    assert mock_threshold_func.call_count == 2
    # assert mock_threshold_func.call_args_list[0] == call()
    # assert result == expected_result

    # Patch each cv2 function that is used. For each one, do assert_called_once_with(...). Also set return value for
    # cv2.threshold and assert binary_img() == this return value


@patch("dodal.devices.i04.beam_centre.cv2.fit_ellipse")
def test_fit_ellipse_good_params(fit_ellipse_mock: MagicMock):
    fit_ellipse_mock.return_value()

    # patch cv2 functiosn and assert_called_once_with, assert return value is correct by setting return value of
    # the cv2.fitellipse magicmock
    pass


def test_fit_ellipse_raises_error_if_not_enough_image_points():
    with pytest.raises(ValueError, match="No contours found in image."):
        pass


def test_fit_ellipse_raises_error_if_not_enough_contour_points():
    pass
