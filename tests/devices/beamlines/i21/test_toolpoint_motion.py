import asyncio
from math import cos, radians, sin

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i21 import (
    ToolPointMotion,
    ToolPointMotorPositions,
    XYZAzimuthTiltPolarParallelPerpendicularStage,
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


async def test_uvw_read(uvw: ToolPointMotion) -> None:
    x, y, z = 5, 10, 15
    dx, dy, dz = x - uvw._zero[0], y - uvw._zero[1], z - uvw._zero[2]
    azimuth_deg, tilt_deg = 10, 30
    azimuth, tilt = radians(azimuth_deg), radians(tilt_deg)

    expected_u = dx * cos(tilt) - dz * sin(tilt)
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

    smp = uvw.smp_ref()
    await asyncio.gather(
        smp.x.set(x),
        smp.y.set(y),
        smp.z.set(z),
        smp.azimuth.set(azimuth_deg),
        smp.tilt.set(tilt_deg),
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


async def test_uvw_u_set(uvw: ToolPointMotion) -> None:
    x, y, z = 5, 10, 15
    azimuth_deg, tilt_deg = 10, 30

    smp = uvw.smp_ref()
    await asyncio.gather(
        smp.x.set(x),
        smp.y.set(y),
        smp.z.set(z),
        smp.azimuth.set(azimuth_deg),
        smp.tilt.set(tilt_deg),
    )

    read = await uvw._read_all()
    u_value = 50
    expected_v = read[1]
    expected_w = read[2]

    await uvw.u.set(u_value)
    await assert_reading(
        uvw,
        {
            uvw.u.name: partial_reading(u_value),
            uvw.v.name: partial_reading(expected_v),
            uvw.w.name: partial_reading(expected_w),
        },
        full_match=False,
    )


async def test_uvw_v_set(uvw: ToolPointMotion) -> None:
    x, y, z = 5, 10, 15
    azimuth_deg, tilt_deg = 10, 30

    smp = uvw.smp_ref()
    await asyncio.gather(
        smp.x.set(x),
        smp.y.set(y),
        smp.z.set(z),
        smp.azimuth.set(azimuth_deg),
        smp.tilt.set(tilt_deg),
    )

    read = await uvw._read_all()
    expected_u = read[0]
    v_value = 50
    expected_w = read[2]

    await uvw.v.set(v_value)
    await assert_reading(
        uvw,
        {
            uvw.u.name: partial_reading(expected_u),
            uvw.v.name: partial_reading(v_value),
            uvw.w.name: partial_reading(expected_w),
        },
        full_match=False,
    )


async def test_uvw_w_set(uvw: ToolPointMotion) -> None:
    x, y, z = 5, 10, 15
    azimuth_deg, tilt_deg = 10, 30

    smp = uvw.smp_ref()
    await asyncio.gather(
        smp.x.set(x),
        smp.y.set(y),
        smp.z.set(z),
        smp.azimuth.set(azimuth_deg),
        smp.tilt.set(tilt_deg),
    )

    read = await uvw._read_all()
    expected_u = read[0]
    expected_v = read[1]
    w_value = 50

    await uvw.w.set(w_value)
    await assert_reading(
        uvw,
        {
            uvw.u.name: partial_reading(expected_u),
            uvw.v.name: partial_reading(expected_v),
            uvw.w.name: partial_reading(w_value),
        },
        full_match=False,
    )


async def test_uvw_set(uvw: ToolPointMotion) -> None:
    pos = ToolPointMotorPositions(x=10, y=20, z=30, tilt=40, azimuth=50)
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

    assert await uvw.smp_ref().azimuth.user_readback.get_value() == pos.azimuth
    assert await uvw.smp_ref().tilt.user_readback.get_value() == pos.tilt
