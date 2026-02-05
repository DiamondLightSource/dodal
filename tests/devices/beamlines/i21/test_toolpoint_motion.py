import asyncio
from math import cos, radians, sin
from unittest.mock import AsyncMock

import numpy as np
import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.epics.motor import MotorLimitsError
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i21 import (
    ToolPointMotion,
    ToolPointMotorPositions,
    XYZAzimuthTiltPolarParallelPerpendicularStage,
)
from dodal.devices.beamlines.i21.toolpoint_motion import (
    DEFAULT_AXES_ZERO,
    toolpoint_to_xyz,
    xyz_to_toolpoint,
)


@pytest.fixture
def smp() -> XYZAzimuthTiltPolarParallelPerpendicularStage:
    with init_devices(mock=True):
        smp = XYZAzimuthTiltPolarParallelPerpendicularStage("TEST:")
    return smp


@pytest.fixture
def uvw(smp: XYZAzimuthTiltPolarParallelPerpendicularStage) -> ToolPointMotion:
    with init_devices(mock=True):
        uvw = ToolPointMotion(smp)
    return uvw


def expected_uvw_read(
    pos: ToolPointMotorPositions, zero: tuple[float, float, float]
) -> tuple[float, float, float]:
    dx, dy, dz = pos.x - zero[0], pos.y - zero[1], pos.z - zero[2]
    azimuth, tilt = radians(pos.azimuth_deg), radians(pos.tilt_deg)
    expected_v = (
        dx * sin(tilt) * sin(azimuth)
        + dy * cos(azimuth)
        + dz * cos(tilt) * sin(azimuth)
    )
    expected_v = (
        dx * sin(tilt) * sin(azimuth)
        + dy * cos(azimuth)
        + dz * cos(tilt) * sin(azimuth)
    )
    expected_w = (
        dx * cos(azimuth) * sin(tilt)
        - dy * sin(azimuth)
        + dz * cos(tilt) * cos(azimuth)
    )
    return expected_v, expected_v, expected_w


def test_toolpoint_math_matches_legacy():
    zero = DEFAULT_AXES_ZERO
    u, v, w = 1.2, -3.4, 5.6
    tilt, azimuth = 30.0, 10.0

    x_new, y_new, z_new = toolpoint_to_xyz(u, v, w, tilt, azimuth, zero)

    chi = radians(tilt)
    phi = radians(azimuth)

    x_old = zero[0] + u * cos(chi) + v * sin(chi) * sin(phi) + w * cos(phi) * sin(chi)
    y_old = zero[1] + v * cos(phi) - w * sin(phi)
    z_old = zero[2] - u * sin(chi) + v * cos(chi) * sin(phi) + w * cos(chi) * cos(phi)

    assert np.allclose([x_new, y_new, z_new], [x_old, y_old, z_old])


def test_xyz_to_toolpoint_matches_legacy():
    zero = DEFAULT_AXES_ZERO

    x, y, z = 12.3, -4.5, 6.7
    tilt, azimuth = 30.0, 10.0

    u_new, v_new, w_new = xyz_to_toolpoint(x, y, z, tilt, azimuth, zero)

    chi = radians(tilt)
    phi = radians(azimuth)

    dx = x - zero[0]
    dy = y - zero[1]
    dz = z - zero[2]

    u_old = dx * cos(chi) - dz * sin(chi)
    v_old = dx * sin(chi) * sin(phi) + dy * cos(phi) + dz * cos(chi) * sin(phi)
    w_old = dx * cos(phi) * sin(chi) - dy * sin(phi) + dz * cos(chi) * cos(phi)

    assert np.allclose(
        [u_new, v_new, w_new],
        [u_old, v_old, w_old],
    )


async def test_uvw_read(uvw: ToolPointMotion) -> None:
    x, y, z = 5.0, 10.0, 15.0
    azimuth_deg, tilt_deg = 10.0, 30.0

    smp = uvw.smp_ref()
    await asyncio.gather(
        smp.x.set(x),
        smp.y.set(y),
        smp.z.set(z),
        smp.azimuth.set(azimuth_deg),
        smp.tilt.set(tilt_deg),
    )
    expected_u, expected_v, expected_w = xyz_to_toolpoint(
        x=x, y=y, z=z, tilt_deg=tilt_deg, azimuth_deg=azimuth_deg, zero=uvw._zero
    )

    smp_read = await smp.read()
    await assert_reading(
        uvw,
        {
            uvw.u.name: partial_reading(expected_u),
            uvw.v.name: partial_reading(expected_v),
            uvw.w.name: partial_reading(expected_w),
        }
        | smp_read,
    )


@pytest.mark.parametrize(
    "axis_name,new_value",
    [
        ("u", 50.0),
        ("v", 40.0),
        ("w", 25.0),
    ],
)
async def test_uvw_axis_set(
    uvw: ToolPointMotion,
    axis_name: str,
    new_value: float,
) -> None:
    azimuth_deg, tilt_deg = 10.0, 30.0
    smp = uvw.smp_ref()

    await asyncio.gather(
        smp.azimuth.set(azimuth_deg),
        smp.tilt.set(tilt_deg),
    )

    # Read initial toolpoint position
    u0, v0, w0, tilt, azimuth = await uvw._read_all()

    # Set the selected axis
    axis = getattr(uvw, axis_name)
    await axis.set(new_value)

    # Build expected toolpoint values
    u = new_value if axis_name == "u" else u0
    v = new_value if axis_name == "v" else v0
    w = new_value if axis_name == "w" else w0

    expected_x, expected_y, expected_z = toolpoint_to_xyz(
        u, v, w, tilt, azimuth, uvw._zero
    )

    actual_x, actual_y, actual_z = await asyncio.gather(
        smp.x.user_readback.get_value(),
        smp.y.user_readback.get_value(),
        smp.z.user_readback.get_value(),
    )

    assert np.isclose(actual_x, expected_x)
    assert np.isclose(actual_y, expected_y)
    assert np.isclose(actual_z, expected_z)

    await assert_reading(
        uvw,
        {
            uvw.u.name: partial_reading(u),
            uvw.v.name: partial_reading(v),
            uvw.w.name: partial_reading(w),
        },
        full_match=False,
    )


async def test_uvw_set(uvw: ToolPointMotion) -> None:
    pos = ToolPointMotorPositions(x=10, y=20, z=30, tilt_deg=40, azimuth_deg=50)
    await uvw.set(pos)

    await assert_reading(
        uvw,
        {
            uvw.u.name: partial_reading(pos.x),
            uvw.v.name: partial_reading(pos.y),
            uvw.w.name: partial_reading(pos.z),
        },
        full_match=False,
    )

    assert await uvw.smp_ref().azimuth.user_readback.get_value() == pos.azimuth_deg
    assert await uvw.smp_ref().tilt.user_readback.get_value() == pos.tilt_deg


@pytest.mark.asyncio
async def test_uvw_check_motor_limits_calls_all_motors(
    uvw: ToolPointMotion,
) -> None:
    smp = uvw.smp_ref()
    smp.x.check_motor_limit = AsyncMock()
    smp.y.check_motor_limit = AsyncMock()
    smp.z.check_motor_limit = AsyncMock()
    smp.tilt.check_motor_limit = AsyncMock()
    smp.azimuth.check_motor_limit = AsyncMock()

    start = ToolPointMotorPositions(
        x=1.0, y=2.0, z=3.0, tilt_deg=10.0, azimuth_deg=20.0
    )
    end = ToolPointMotorPositions(x=4.0, y=5.0, z=6.0, tilt_deg=30.0, azimuth_deg=40.0)

    await uvw.check_motor_limits(start, end)

    smp.x.check_motor_limit.assert_awaited_once_with(start.x, end.x)
    smp.y.check_motor_limit.assert_awaited_once_with(start.y, end.y)
    smp.z.check_motor_limit.assert_awaited_once_with(start.z, end.z)
    smp.tilt.check_motor_limit.assert_awaited_once_with(start.tilt_deg, end.tilt_deg)
    smp.azimuth.check_motor_limit.assert_awaited_once_with(
        start.azimuth_deg, end.azimuth_deg
    )


@pytest.mark.asyncio
async def test_check_motor_limits_raises_on_failure(
    uvw: ToolPointMotion,
) -> None:
    set_mock_value(uvw.smp_ref().z.high_limit_travel, 500)
    set_mock_value(uvw.smp_ref().z.dial_high_limit_travel, 500)

    start = ToolPointMotorPositions(x=0.0, y=0.0, z=0.0, tilt_deg=0.0, azimuth_deg=0.0)
    end = ToolPointMotorPositions(x=1.0, y=1.0, z=600, tilt_deg=5.0, azimuth_deg=5.0)

    with pytest.raises(MotorLimitsError):
        await uvw.check_motor_limits(start, end)
