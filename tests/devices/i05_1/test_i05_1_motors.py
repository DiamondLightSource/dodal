import asyncio
from math import cos, radians, sin

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i05_1 import XYZPolarAzimuthDefocusStage
from tests.devices.i05_shared.rotation_signal_test_util import (
    AxesTestConfig,
    assert_set_axis_preserves_other,
)


@pytest.fixture
def xyzpad_stage() -> XYZPolarAzimuthDefocusStage:
    with init_devices(mock=True):
        xyzpad_stage = XYZPolarAzimuthDefocusStage("TEST:")
    return xyzpad_stage


def expected_hor_read(x: float, y: float, azimuth_theta: float) -> float:
    return x * cos(azimuth_theta) + y * sin(azimuth_theta)


def expected_vert_read(x: float, y: float, azimuth_theta: float) -> float:
    return x * -sin(azimuth_theta) + y * cos(azimuth_theta)


def expected_long_read(z: float, hor: float, polar_theta: float) -> float:
    return z * cos(polar_theta) + hor * -sin(polar_theta)


def expected_perp_read(z: float, hor: float, polar_theta: float) -> float:
    return z * sin(polar_theta) + hor * cos(polar_theta)


async def test_xyzpad_stage_read(xyzpad_stage: XYZPolarAzimuthDefocusStage) -> None:
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
        xyzpad_stage.x.set(x),
        xyzpad_stage.y.set(y),
        xyzpad_stage.z.set(z),
        xyzpad_stage.azimuth.set(azimuth_angle_deg),
        xyzpad_stage.polar.set(polar_angle_deg),
    )

    await assert_reading(
        xyzpad_stage,
        {
            xyzpad_stage.x.name: partial_reading(x),
            xyzpad_stage.y.name: partial_reading(y),
            xyzpad_stage.z.name: partial_reading(z),
            xyzpad_stage.polar.name: partial_reading(polar_angle_deg),
            xyzpad_stage.azimuth.name: partial_reading(azimuth_angle_deg),
            xyzpad_stage.defocus.name: partial_reading(0),
            xyzpad_stage.hor.name: partial_reading(expected_hor),
            xyzpad_stage.vert.name: partial_reading(expected_vert),
            xyzpad_stage.long.name: partial_reading(expected_long),
            xyzpad_stage.perp.name: partial_reading(expected_perp),
        },
    )


async def test_xyzpad_hor_and_vert_set(
    xyzpad_stage: XYZPolarAzimuthDefocusStage,
) -> None:
    axes_test_config = AxesTestConfig(
        i_read=xyzpad_stage.x.user_readback,
        j_read=xyzpad_stage.y.user_readback,
        i_write=xyzpad_stage.x,
        j_write=xyzpad_stage.y,
        angle_deg=xyzpad_stage.azimuth,
        expected_i_read_func=expected_hor_read,
        expected_j_read_func=expected_vert_read,
        i_rotation_axis=xyzpad_stage.hor,
        j_rotation_axis=xyzpad_stage.vert,
    )

    await assert_set_axis_preserves_other(
        i_val=10,
        j_val=5,
        angle_deg_val=45,
        new_i_axis_value=20,
        new_j_axis_value=20,
        axes_config=axes_test_config,
    )


async def test_xyzpad_long_and_perp_set(
    xyzpad_stage: XYZPolarAzimuthDefocusStage,
) -> None:
    axes_test_config = AxesTestConfig(
        i_read=xyzpad_stage.z.user_readback,
        j_read=xyzpad_stage.hor,
        i_write=xyzpad_stage.z,
        j_write=xyzpad_stage.hor,
        angle_deg=xyzpad_stage.polar,
        expected_i_read_func=expected_long_read,
        expected_j_read_func=expected_perp_read,
        i_rotation_axis=xyzpad_stage.long,
        j_rotation_axis=xyzpad_stage.perp,
    )

    await assert_set_axis_preserves_other(
        i_val=10,
        j_val=5,
        angle_deg_val=45,
        new_i_axis_value=20,
        new_j_axis_value=20,
        axes_config=axes_test_config,
    )
