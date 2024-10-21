from unittest.mock import AsyncMock

import numpy as np
import pytest
from bluesky.run_engine import RunEngine
from ophyd.sim import instantiate_fake_device

# from ophyd_async.core import set_mock_value
from dodal.devices.oav.oav_calculations import calculate_beam_distance
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.oav.pin_image_recognition.utils import SampleLocation
from dodal.devices.oav.utils import (
    PinNotFoundException,
    bottom_right_from_top_left,
    wait_for_tip_to_be_found,
    # get_move_required_so_that_beam_is_at_pixel,
)

# from dodal.devices.smargon import Smargon


def test_bottom_right_from_top_left():
    top_left = np.array([123, 123])
    bottom_right = bottom_right_from_top_left(
        top_left, 20, 30, 0.1, 0.15, 2.7027, 2.7027
    )
    assert bottom_right[0] == 863 and bottom_right[1] == 1788
    bottom_right = bottom_right_from_top_left(top_left, 15, 20, 0.005, 0.007, 1, 1)
    assert bottom_right[0] == 198 and bottom_right[1] == 263


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


# TODO, can't set beam center and micron as I want, will need to calculate
# the right values.
# @pytest.mark.parametrize(
#     "px_per_um, beam_centre, angle, pixel_to_move_to, expected_xyz",
#     [
#         # Simple case of beam being in the top left and each pixel being 1 mm
#         ([1000, 1000], [0, 0], 0, [100, 190], [100, 190, 0]),
#         ([1000, 1000], [0, 0], -90, [50, 250], [50, 0, 250]),
#         ([1000, 1000], [0, 0], 90, [-60, 450], [-60, 0, -450]),
#         # Beam offset
#         ([1000, 1000], [100, 100], 0, [100, 100], [0, 0, 0]),
#         ([1000, 1000], [100, 100], -90, [50, 250], [-50, 0, 150]),
#         # Pixels_per_micron different
#         ([10, 50], [0, 0], 0, [100, 190], [1, 9.5, 0]),
#         ([60, 80], [0, 0], -90, [50, 250], [3, 0, 20]),
#     ],
# )
# async def test_values_for_move_so_that_beam_is_at_pixel(
#     smargon: Smargon,
#     oav: OAV,
#     px_per_um,
#     beam_centre,
#     angle,
#     pixel_to_move_to,
#     expected_xyz,
# ):
#     await oav.microns_per_pixel_x._backend.put(px_per_um[0])
#     # set_mock_value(oav.microns_per_pixel_x, px_per_um[0])
#     set_mock_value(oav.microns_per_pixel_y, px_per_um[1])
#     set_mock_value(oav.beam_centre_i, beam_centre[0])
#     set_mock_value(oav.beam_centre_j, beam_centre[1])

#     set_mock_value(smargon.omega.user_readback, angle)

#     RE = RunEngine(call_returns_result=True)
#     pos = RE(
#         get_move_required_so_that_beam_is_at_pixel(
#             smargon, pixel_to_move_to, oav
#         )
#     ).plan_result  # type: ignore

#     assert pos == pytest.approx(expected_xyz)


@pytest.mark.asyncio
async def test_given_tip_found_when_wait_for_tip_to_be_found_called_then_tip_immediately_returned():
    mock_pin_tip_detect: PinTipDetection = instantiate_fake_device(
        PinTipDetection, name="pin_detect"
    )
    await mock_pin_tip_detect.connect(mock=True)
    mock_pin_tip_detect._get_tip_and_edge_data = AsyncMock(
        return_value=SampleLocation(100, 100, np.array([]), np.array([]))
    )
    RE = RunEngine(call_returns_result=True)
    result = RE(wait_for_tip_to_be_found(mock_pin_tip_detect))
    assert result.plan_result == (100, 100)  # type: ignore
    mock_pin_tip_detect._get_tip_and_edge_data.assert_called_once()


@pytest.mark.asyncio
async def test_given_no_tip_when_wait_for_tip_to_be_found_called_then_exception_thrown():
    mock_pin_tip_detect: PinTipDetection = instantiate_fake_device(
        PinTipDetection, name="pin_detect"
    )
    await mock_pin_tip_detect.connect(mock=True)
    await mock_pin_tip_detect.validity_timeout.set(0.2)
    mock_pin_tip_detect._get_tip_and_edge_data = AsyncMock(
        return_value=SampleLocation(
            *PinTipDetection.INVALID_POSITION, np.array([]), np.array([])
        )
    )
    RE = RunEngine(call_returns_result=True)
    with pytest.raises(PinNotFoundException):
        RE(wait_for_tip_to_be_found(mock_pin_tip_detect))
