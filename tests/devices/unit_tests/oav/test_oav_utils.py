from unittest.mock import AsyncMock

import numpy as np
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.oav.oav_calculations import calculate_beam_distance
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.oav.pin_image_recognition.utils import SampleLocation
from dodal.devices.oav.utils import (
    PinNotFoundException,
    bottom_right_from_top_left,
    get_move_required_so_that_beam_is_at_pixel,
    wait_for_tip_to_be_found,
)
from dodal.devices.smargon import Smargon
from dodal.devices.util.test_utils import patch_motor


def test_bottom_right_from_top_left():
    top_left = np.array([123, 123])
    bottom_right = bottom_right_from_top_left(
        top_left, 20, 30, 0.1, 0.15, 2.7027, 2.7027
    )
    assert bottom_right[0] == 863 and bottom_right[1] == 1788
    bottom_right = bottom_right_from_top_left(top_left, 15, 20, 0.005, 0.007, 1, 1)
    assert bottom_right[0] == 198 and bottom_right[1] == 263


@pytest.fixture
async def smargon(RE: RunEngine):
    async with init_devices(mock=True):
        smargon = Smargon()

    for motor in [smargon.omega, smargon.x, smargon.y, smargon.z]:
        patch_motor(motor)

    return smargon


@pytest.mark.parametrize(
    "h, v, expected_x, expected_y",
    [
        (54, 100, 517 - 54, 350 - 100),
        (0, 0, 517, 350),
        (500, 500, 517 - 500, 350 - 500),
    ],
)
def test_calculate_beam_distance(h, v, expected_x, expected_y, oav: OAV):
    # Beam center from test files for zoom_level = 5.0x
    beam_centre = (517, 350)

    assert calculate_beam_distance(
        beam_centre,
        h,
        v,
    ) == (expected_x, expected_y)


@pytest.mark.parametrize(
    "zoom_level, angle, pixel_to_move_to, expected_xyz",
    [
        # Different zoom levels -> different um_per_pix and beam_centre
        ("5.0x", 0, (100, 190), (-0.659, -0.253, 0)),
        ("1.0x", 0, (100, 190), (-1.082, -0.485, 0)),
        # Different position to reach, same zoom level
        ("1.0x", 0, (50, 250), (-1.226, -0.313, 0)),
        # Change angle
        ("5.0x", 45, (100, 190), (-0.659, -0.179, 0.179)),
    ],
)
async def test_values_for_move_so_that_beam_is_at_pixel(
    zoom_level: str,
    angle: int,
    pixel_to_move_to: tuple,
    expected_xyz: tuple,
    oav: OAV,
    smargon: Smargon,
):
    set_mock_value(oav.zoom_controller.level, zoom_level)
    set_mock_value(smargon.omega.user_readback, angle)
    RE = RunEngine(call_returns_result=True)
    pos = RE(
        get_move_required_so_that_beam_is_at_pixel(smargon, pixel_to_move_to, oav)
    ).plan_result  # type: ignore

    assert pos == pytest.approx(expected_xyz, abs=1e-3)


async def test_given_tip_found_when_wait_for_tip_to_be_found_called_then_tip_immediately_returned(
    RE,
):
    async with init_devices(mock=True):
        mock_pin_tip_detect = PinTipDetection("")

    await mock_pin_tip_detect.connect(mock=True)
    mock_pin_tip_detect._get_tip_and_edge_data = AsyncMock(
        return_value=SampleLocation(100, 100, np.array([]), np.array([]))
    )
    RE = RunEngine(call_returns_result=True)
    result = RE(wait_for_tip_to_be_found(mock_pin_tip_detect))
    assert result.plan_result == (100, 100)  # type: ignore
    mock_pin_tip_detect._get_tip_and_edge_data.assert_called_once()


async def test_given_no_tip_when_wait_for_tip_to_be_found_called_then_exception_thrown():
    async with init_devices(mock=True):
        mock_pin_tip_detect = PinTipDetection("")

    await mock_pin_tip_detect.connect(mock=True)
    await mock_pin_tip_detect.validity_timeout.set(0.2)
    mock_pin_tip_detect._get_tip_and_edge_data = AsyncMock(
        return_value=SampleLocation(
            int(PinTipDetection.INVALID_POSITION[0]),
            int(PinTipDetection.INVALID_POSITION[1]),
            np.array([]),
            np.array([]),
        )
    )
    RE = RunEngine(call_returns_result=True)
    with pytest.raises(PinNotFoundException):
        RE(wait_for_tip_to_be_found(mock_pin_tip_detect))
