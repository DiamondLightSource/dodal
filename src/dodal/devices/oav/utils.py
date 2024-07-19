from enum import IntEnum
from typing import Generator, Tuple

import bluesky.plan_stubs as bps
import numpy as np
from bluesky.utils import Msg

from dodal.devices.oav.oav_calculations import camera_coordinates_to_xyz
from dodal.devices.oav.oav_detector import OAVConfigParams
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.smargon import Smargon

Pixel = Tuple[int, int]


class PinNotFoundException(Exception):
    pass


def bottom_right_from_top_left(
    top_left: np.ndarray,
    steps_x: int,
    steps_y: int,
    step_size_x: float,
    step_size_y: float,
    um_per_pix_x: float,
    um_per_pix_y: float,
) -> np.ndarray:
    return np.array(
        [
            # step size is given in mm, pix in um
            int(steps_x * step_size_x * 1000 / um_per_pix_x + top_left[0]),
            int(steps_y * step_size_y * 1000 / um_per_pix_y + top_left[1]),
        ],
        dtype=np.dtype(int),
    )


class ColorMode(IntEnum):
    """
    Enum to store the various color modes of the camera. We use RGB1.
    """

    MONO = 0
    BAYER = 1
    RGB1 = 2
    RGB2 = 3
    RGB3 = 4
    YUV444 = 5
    YUV422 = 6
    YUV421 = 7


class EdgeOutputArrayImageType(IntEnum):
    """
    Enum to store the types of image to tweak the output array. We use Original.
    """

    ORIGINAL = 0
    GREYSCALE = 1
    PREPROCESSED = 2
    CANNY_EDGES = 3
    CLOSED_EDGES = 4


def get_move_required_so_that_beam_is_at_pixel(
    smargon: Smargon, pixel: Pixel, oav_params: OAVConfigParams
) -> Generator[Msg, None, np.ndarray]:
    """Calculate the required move so that the given pixel is in the centre of the beam."""

    current_motor_xyz = np.array(
        [
            (yield from bps.rd(smargon.x)),
            (yield from bps.rd(smargon.y)),
            (yield from bps.rd(smargon.z)),
        ],
        dtype=np.float64,
    )
    current_angle = yield from bps.rd(smargon.omega)

    return calculate_x_y_z_of_pixel(current_motor_xyz, current_angle, pixel, oav_params)


def calculate_x_y_z_of_pixel(
    current_x_y_z, current_omega, pixel: Pixel, oav_params: OAVConfigParams
) -> np.ndarray:
    beam_distance_px: Pixel = oav_params.calculate_beam_distance(*pixel)

    assert oav_params.micronsPerXPixel
    assert oav_params.micronsPerYPixel
    return current_x_y_z + camera_coordinates_to_xyz(
        beam_distance_px[0],
        beam_distance_px[1],
        current_omega,
        oav_params.micronsPerXPixel,
        oav_params.micronsPerYPixel,
    )


def wait_for_tip_to_be_found(
    ophyd_pin_tip_detection: PinTipDetection,
) -> Generator[Msg, None, Pixel]:
    yield from bps.trigger(ophyd_pin_tip_detection, wait=True)
    found_tip = yield from bps.rd(ophyd_pin_tip_detection.triggered_tip)
    if found_tip == ophyd_pin_tip_detection.INVALID_POSITION:
        timeout = yield from bps.rd(ophyd_pin_tip_detection.validity_timeout)
        raise PinNotFoundException(f"No pin found after {timeout} seconds")

    return found_tip  # type: ignore
