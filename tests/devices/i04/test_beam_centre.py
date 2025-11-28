from collections.abc import AsyncGenerator
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from ophyd_async.core import init_devices, set_mock_value

from dodal.devices.i04.beam_center import CentreEllipseMethod


@pytest.fixture
async def beam_centre_ellipse() -> AsyncGenerator[CentreEllipseMethod]:
    async with init_devices(mock=True):
        max_pixel = CentreEllipseMethod("TEST: ELLIPSE_CENTRE")
    yield max_pixel


@patch("dodal.devices.i04.max_pixel.cv2.GaussianBlur")
def test_binary_img():
    pass

    # Patch each cv2 function that is used. For each one, do assert_called_once_with(...). Also set return value for
    # cv2.threshold and assert binary_img() == this return value


def test_fit_ellipse_good_params():
    # patch cv2 functiosn and assert_called_once_with, assert return value is correct by setting return value of
    # the cv2.fitellipse magicmock
    pass


def test_fit_ellipse_raises_error_if_not_enough_image_points():
    with pytest.raises(ValueError, match="No contours found in image."):
        pass


def test_fit_ellipse_raises_error_if_not_enough_contour_points():
    pass
