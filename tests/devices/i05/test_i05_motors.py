import asyncio
from math import cos, radians, sin

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i05 import I05Goniometer
from tests.devices.i05_shared.rotation_signal_test_util import (
    AxesTestConfig,
    assert_set_axis_preserves_other,
)


def expected_perp_read(x: float, y: float, theta: float) -> float:
    return x * cos(theta) + y * sin(theta)


def expected_long_read(x: float, y: float, theta: float) -> float:
    return x * -sin(theta) + y * cos(theta)


@pytest.fixture
async def goniometer():
    with init_devices(mock=True):
        goniometer = I05Goniometer("TEST:")
    return goniometer


async def test_goniometer_read(goniometer: I05Goniometer) -> None:
    x, y = 10, 5
    theta = radians(goniometer.rotation_angle_deg)
    expected_perp = expected_perp_read(x, y, theta)
    expected_long = expected_long_read(x, y, theta)

    await asyncio.gather(goniometer.x.set(x), goniometer.y.set(y))

    await assert_reading(
        goniometer,
        {
            goniometer.x.name: partial_reading(x),
            goniometer.y.name: partial_reading(y),
            goniometer.z.name: partial_reading(0),
            goniometer.polar.name: partial_reading(0),
            goniometer.azimuth.name: partial_reading(0),
            goniometer.tilt.name: partial_reading(0),
            goniometer.perp.name: partial_reading(expected_perp),
            goniometer.long.name: partial_reading(expected_long),
        },
    )


async def test_goniometer_perp_and_long_set(
    goniometer: I05Goniometer,
) -> None:
    axes_test_config = AxesTestConfig(
        i_read=goniometer.x.user_readback,
        j_read=goniometer.y.user_readback,
        i_write=goniometer.x,  # type: ignore
        j_write=goniometer.y,  # type: ignore
        angle_deg=goniometer.rotation_angle_deg,
        expected_i_read_func=expected_perp_read,
        expected_j_read_func=expected_long_read,
        i_rotation_axis=goniometer.perp,
        j_rotation_axis=goniometer.long,
    )

    await assert_set_axis_preserves_other(
        i_val=10,
        j_val=5,
        angle_deg_val=goniometer.rotation_angle_deg,
        new_i_axis_value=20,
        new_j_axis_value=20,
        axes_config=axes_test_config,
    )
