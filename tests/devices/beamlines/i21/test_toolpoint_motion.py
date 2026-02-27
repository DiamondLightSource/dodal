import asyncio
from dataclasses import replace
from math import cos, radians, sin
from unittest.mock import AsyncMock

import numpy as np
import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.epics.motor import MotorLimitsError
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i21 import (
    I21SampleManipulatorStage,
    ToolPointMotion,
    UVWMotorPositions,
    XYZMotorPositions,
)
from dodal.devices.beamlines.i21.toolpoint_motion import (
    DEFAULT_AXES_ZERO,
    uvw_to_xyz,
    xyz_to_uvw,
)


@pytest.fixture
def smp() -> I21SampleManipulatorStage:
    with init_devices(mock=True):
        smp = I21SampleManipulatorStage("TEST:")
    return smp


@pytest.fixture
def uvw(smp: I21SampleManipulatorStage) -> ToolPointMotion:
    with init_devices(mock=True):
        uvw = ToolPointMotion(smp)
    return uvw


def expected_uvw_read(
    pos: XYZMotorPositions, zero: tuple[float, float, float]
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


def test_uvw_to_xyz_math_matches_legacy():
    zero = DEFAULT_AXES_ZERO
    u, v, w = 1.2, -3.4, 5.6
    tilt, azimuth = 30.0, 10.0

    uvw = UVWMotorPositions(u=u, v=v, w=w, tilt_deg=tilt, azimuth_deg=azimuth)

    expected_xyz = uvw_to_xyz(uvw, zero)

    chi = radians(tilt)
    phi = radians(azimuth)

    x_legacy = (
        zero[0] + u * cos(chi) + v * sin(chi) * sin(phi) + w * cos(phi) * sin(chi)
    )
    y_legacy = zero[1] + v * cos(phi) - w * sin(phi)
    z_legacy = (
        zero[2] - u * sin(chi) + v * cos(chi) * sin(phi) + w * cos(chi) * cos(phi)
    )
    assert np.allclose(
        [x_legacy, y_legacy, z_legacy], [expected_xyz.x, expected_xyz.y, expected_xyz.z]
    )


def test_xyz_to_uvw_math_matches_legacy():
    zero = DEFAULT_AXES_ZERO

    x, y, z = 12.3, -4.5, 6.7
    tilt, azimuth = 30.0, 10.0
    xyz = XYZMotorPositions(x=x, y=y, z=z, tilt_deg=tilt, azimuth_deg=azimuth)

    expected_uvw = xyz_to_uvw(xyz, zero)

    chi = radians(tilt)
    phi = radians(azimuth)

    dx = x - zero[0]
    dy = y - zero[1]
    dz = z - zero[2]

    u_legacy = dx * cos(chi) - dz * sin(chi)
    v_legacy = dx * sin(chi) * sin(phi) + dy * cos(phi) + dz * cos(chi) * sin(phi)
    w_legacy = dx * cos(phi) * sin(chi) - dy * sin(phi) + dz * cos(chi) * cos(phi)

    assert np.allclose(
        [u_legacy, v_legacy, w_legacy], [expected_uvw.u, expected_uvw.v, expected_uvw.w]
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
    xyz_pos = XYZMotorPositions(
        x=x, y=y, z=z, tilt_deg=tilt_deg, azimuth_deg=azimuth_deg
    )
    expected_uvw = xyz_to_uvw(xyz_pos, zero=uvw._zero)

    smp_read = await smp.read()
    await assert_reading(
        uvw,
        {
            uvw.u.name: partial_reading(expected_uvw.u),
            uvw.v.name: partial_reading(expected_uvw.v),
            uvw.w.name: partial_reading(expected_uvw.w),
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
    uvw_pos0 = await uvw._read_all_uvw()

    # Set the selected axis
    axis = getattr(uvw, axis_name)
    await axis.set(new_value)

    # Build expected toolpoint values
    uvw_pos = replace(uvw_pos0, **{axis_name: new_value})

    expected_xyz = uvw_to_xyz(uvw_pos, uvw._zero)

    actual_x, actual_y, actual_z = await asyncio.gather(
        smp.x.user_readback.get_value(),
        smp.y.user_readback.get_value(),
        smp.z.user_readback.get_value(),
    )

    assert np.isclose(actual_x, expected_xyz.x)
    assert np.isclose(actual_y, expected_xyz.y)
    assert np.isclose(actual_z, expected_xyz.z)

    await assert_reading(
        uvw,
        {
            uvw.u.name: partial_reading(uvw_pos.u),
            uvw.v.name: partial_reading(uvw_pos.v),
            uvw.w.name: partial_reading(uvw_pos.w),
        },
        full_match=False,
    )


async def test_uvw_set(uvw: ToolPointMotion) -> None:
    pos = UVWMotorPositions(u=10, v=20, w=30, tilt_deg=40, azimuth_deg=50)
    await uvw.set(pos)

    await assert_reading(
        uvw,
        {
            uvw.u.name: partial_reading(pos.u),
            uvw.v.name: partial_reading(pos.v),
            uvw.w.name: partial_reading(pos.w),
        },
        full_match=False,
    )

    assert await uvw.smp_ref().azimuth.user_readback.get_value() == pos.azimuth_deg
    assert await uvw.smp_ref().tilt.user_readback.get_value() == pos.tilt_deg


async def test_uvw_check_motor_limits_calls_all_motors(
    uvw: ToolPointMotion,
) -> None:
    smp = uvw.smp_ref()
    smp.x.check_motor_limit = AsyncMock()
    smp.y.check_motor_limit = AsyncMock()
    smp.z.check_motor_limit = AsyncMock()
    smp.tilt.check_motor_limit = AsyncMock()
    smp.azimuth.check_motor_limit = AsyncMock()

    start = XYZMotorPositions(x=1.0, y=2.0, z=3.0, tilt_deg=10.0, azimuth_deg=20.0)
    end = XYZMotorPositions(x=4.0, y=5.0, z=6.0, tilt_deg=30.0, azimuth_deg=40.0)

    await uvw.check_motor_limits(start, end)

    smp.x.check_motor_limit.assert_awaited_once_with(start.x, end.x)
    smp.y.check_motor_limit.assert_awaited_once_with(start.y, end.y)
    smp.z.check_motor_limit.assert_awaited_once_with(start.z, end.z)
    smp.tilt.check_motor_limit.assert_awaited_once_with(start.tilt_deg, end.tilt_deg)
    smp.azimuth.check_motor_limit.assert_awaited_once_with(
        start.azimuth_deg, end.azimuth_deg
    )


async def test_check_motor_limits_raises_on_failure(
    uvw: ToolPointMotion,
) -> None:
    set_mock_value(uvw.smp_ref().z.high_limit_travel, 500)
    set_mock_value(uvw.smp_ref().z.dial_high_limit_travel, 500)

    start = XYZMotorPositions(x=0.0, y=0.0, z=0.0, tilt_deg=0.0, azimuth_deg=0.0)
    end = XYZMotorPositions(x=1.0, y=1.0, z=600, tilt_deg=5.0, azimuth_deg=5.0)

    with pytest.raises(MotorLimitsError):
        await uvw.check_motor_limits(start, end)
