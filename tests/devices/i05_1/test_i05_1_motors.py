import asyncio
from math import cos, radians, sin

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i05_1 import XYZPolarAzimuthDefocusStage


@pytest.fixture
def xyzpad_stage() -> XYZPolarAzimuthDefocusStage:
    with init_devices(mock=True):
        xyzpad_stage = XYZPolarAzimuthDefocusStage("TEST:")
    return xyzpad_stage


async def test_xyzpad_stage_read(xyzpad_stage: XYZPolarAzimuthDefocusStage) -> None:
    x, y = 10, 5
    azimuth_angle_deg = 45
    azimuth_theta = radians(azimuth_angle_deg)
    expected_hor = x * cos(azimuth_theta) + y * sin(azimuth_theta)
    expected_vert = x * -sin(azimuth_theta) + y * cos(azimuth_theta)

    z = 15
    polar_angle_deg = 35
    polar_theta = radians(polar_angle_deg)
    expected_long = z * cos(polar_theta) + expected_hor * -sin(polar_theta)
    expected_perp = z * sin(polar_theta) + expected_hor * cos(polar_theta)

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
