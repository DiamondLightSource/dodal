import asyncio
from math import cos, radians, sin

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i05_1 import XYZPolarAzimuthDefocusStage
from tests.devices.beamlines.i05_shared.rotation_signal_test_util import (
    RotatedCartesianFrameTestConfig,
    assert_rotated_axes_are_orthogonal,
)


@pytest.fixture
def sm() -> XYZPolarAzimuthDefocusStage:
    with init_devices(mock=True):
        sm = XYZPolarAzimuthDefocusStage("TEST:")
    return sm


def expected_hor_read(x: float, y: float, azimuth_theta: float) -> float:
    return x * cos(azimuth_theta) + y * sin(azimuth_theta)


def expected_vert_read(x: float, y: float, azimuth_theta: float) -> float:
    return x * -sin(azimuth_theta) + y * cos(azimuth_theta)


def expected_long_read(z: float, hor: float, polar_theta: float) -> float:
    return z * cos(polar_theta) + hor * -sin(polar_theta)


def expected_perp_read(z: float, hor: float, polar_theta: float) -> float:
    return z * sin(polar_theta) + hor * cos(polar_theta)


async def test_xyzpad_stage_read(sm: XYZPolarAzimuthDefocusStage) -> None:
    x, y = 10, 5
    azimuth_angle_deg = 45
    azimuth_theta = radians(azimuth_angle_deg)
    expected_hor = expected_hor_read(x, y, azimuth_theta)
    expected_vert = expected_vert_read(x, y, azimuth_theta)

    z = 15
    polar_angle_deg = 35
    polar_theta = radians(polar_angle_deg)
    expected_long = expected_long_read(z, expected_hor, polar_theta)
    expected_perp = expected_perp_read(z, expected_hor, polar_theta)

    await asyncio.gather(
        sm.x.set(x),
        sm.y.set(y),
        sm.z.set(z),
        sm.azimuth.set(azimuth_angle_deg),
        sm.polar.set(polar_angle_deg),
    )
    await assert_reading(
        sm,
        {
            sm.x.name: partial_reading(x),
            sm.y.name: partial_reading(y),
            sm.z.name: partial_reading(z),
            sm.polar.name: partial_reading(polar_angle_deg),
            sm.azimuth.name: partial_reading(azimuth_angle_deg),
            sm.defocus.name: partial_reading(0),
            sm.hor.name: partial_reading(expected_hor),
            sm.vert.name: partial_reading(expected_vert),
            sm.long.name: partial_reading(expected_long),
            sm.perp.name: partial_reading(expected_perp),
        },
    )


async def test_xyzpad_hor_and_vert_set(
    sm: XYZPolarAzimuthDefocusStage,
) -> None:
    frame_config = RotatedCartesianFrameTestConfig(
        i_read=sm.x.user_readback,
        j_read=sm.y.user_readback,
        i_write=sm.x,
        j_write=sm.y,
        angle_deg=sm.azimuth,
        expected_i_read_func=expected_hor_read,
        expected_j_read_func=expected_vert_read,
        i_rotation_axis=sm.hor,
        j_rotation_axis=sm.vert,
    )
    await assert_rotated_axes_are_orthogonal(
        i_val=10,
        j_val=5,
        angle_deg_val=45,
        new_i_axis_value=20,
        new_j_axis_value=20,
        frame_config=frame_config,
    )


async def test_xyzpad_long_and_perp_set(
    sm: XYZPolarAzimuthDefocusStage,
) -> None:
    frame_config = RotatedCartesianFrameTestConfig(
        i_read=sm.z.user_readback,
        j_read=sm.hor,
        i_write=sm.z,
        j_write=sm.hor,
        angle_deg=sm.polar,
        expected_i_read_func=expected_long_read,
        expected_j_read_func=expected_perp_read,
        i_rotation_axis=sm.long,
        j_rotation_axis=sm.perp,
    )
    await assert_rotated_axes_are_orthogonal(
        i_val=10,
        j_val=5,
        angle_deg_val=45,
        new_i_axis_value=20,
        new_j_axis_value=20,
        frame_config=frame_config,
    )
