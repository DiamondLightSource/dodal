import asyncio
from math import radians

import pytest
from numpy import cos, sin
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i05_1 import XYZPolarAzimuthDefocusStage


@pytest.fixture
def xyzpad_stage() -> XYZPolarAzimuthDefocusStage:
    with init_devices(mock=True):
        xyzpad_stage = XYZPolarAzimuthDefocusStage("TEST:")
    return xyzpad_stage


async def test_goniometer_read(xyzpad_stage: XYZPolarAzimuthDefocusStage) -> None:
    x, y = 10, 5
    angle_deg = 45
    theta = radians(angle_deg)

    expected_horz = x * cos(theta) + y * sin(theta)
    expected_vert = x * -sin(theta) + y * cos(theta)

    await asyncio.gather(
        xyzpad_stage.x.set(x),
        xyzpad_stage.y.set(y),
        xyzpad_stage.azimuth.set(angle_deg),
    )

    await assert_reading(
        xyzpad_stage,
        {
            xyzpad_stage.x.name: partial_reading(x),
            xyzpad_stage.y.name: partial_reading(y),
            xyzpad_stage.z.name: partial_reading(0),
            xyzpad_stage.polar.name: partial_reading(0),
            xyzpad_stage.azimuth.name: partial_reading(angle_deg),
            xyzpad_stage.defocus.name: partial_reading(0),
            xyzpad_stage.hor.name: partial_reading(expected_horz),
            xyzpad_stage.vert.name: partial_reading(expected_vert),
        },
    )


@pytest.mark.parametrize(
    "x, y, z, polar, azimuth, defocus",
    [
        (0, 0, 0, 0, 0, 0),
        (1.23, 2.40, 0.0, 0.0, 0.0, 0.0),
        (1.23, 2.40, 3.51, 24.0, 1.0, 2.0),
    ],
)
async def test_setting_xyzpad_position_table(
    xyzpad_stage: XYZPolarAzimuthDefocusStage,
    x: float,
    y: float,
    z: float,
    polar: float,
    azimuth: float,
    defocus: float,
) -> None:
    set_mock_value(xyzpad_stage.x.user_readback, x)
    set_mock_value(xyzpad_stage.y.user_readback, y)
    set_mock_value(xyzpad_stage.z.user_readback, z)
    set_mock_value(xyzpad_stage.polar.user_readback, polar)
    set_mock_value(xyzpad_stage.azimuth.user_readback, azimuth)
    set_mock_value(xyzpad_stage.defocus.user_readback, defocus)

    await assert_reading(
        xyzpad_stage,
        {
            "xyzpad_stage-x": partial_reading(x),
            "xyzpad_stage-y": partial_reading(y),
            "xyzpad_stage-z": partial_reading(z),
            "xyzpad_stage-polar": partial_reading(polar),
            "xyzpad_stage-azimuth": partial_reading(azimuth),
            "xyzpad_stage-defocus": partial_reading(defocus),
        },
    )
