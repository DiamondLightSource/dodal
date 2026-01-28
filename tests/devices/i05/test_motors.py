import asyncio
from math import cos, sin

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i05.motors import THETA, I05Goniometer


@pytest.fixture
async def goniometer():
    with init_devices(mock=True):
        goniometer = I05Goniometer("TEST:")
    return goniometer


async def test_goniometer_read(goniometer: I05Goniometer) -> None:
    x = 10.0
    y = 5.0
    expected_long = y * cos(THETA) - x * sin(THETA)
    expected_perp = y * sin(THETA) + x * cos(THETA)

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


async def test_goniometer_set_long(goniometer: I05Goniometer) -> None:
    x, y = 10, 5
    await asyncio.gather(goniometer.x.set(x), goniometer.y.set(y))

    perp_before = goniometer._read_perp_calc(x, y)

    new_long = 20.0
    await goniometer.long.set(new_long)

    x_new = await goniometer.x.user_readback.get_value()
    y_new = await goniometer.y.user_readback.get_value()

    long_after = goniometer._read_long_calc(x_new, y_new)
    perp_after = goniometer._read_perp_calc(x_new, y_new)

    assert long_after == pytest.approx(new_long)
    assert perp_after == pytest.approx(perp_before)


async def test_goniometer_set_perp(goniometer: I05Goniometer) -> None:
    x, y = 10.0, 5.0
    await asyncio.gather(goniometer.x.set(x), goniometer.y.set(y))

    long_before = goniometer._read_long_calc(x, y)

    new_perp = 15.0
    await goniometer.perp.set(new_perp)

    x_new_perp = await goniometer.x.user_readback.get_value()
    y_new_perp = await goniometer.y.user_readback.get_value()

    long_after_perp = goniometer._read_long_calc(x_new_perp, y_new_perp)
    perp_after_perp = goniometer._read_perp_calc(x_new_perp, y_new_perp)

    assert perp_after_perp == pytest.approx(new_perp, abs=1e-5)
    assert long_after_perp == pytest.approx(long_before, abs=1e-5)
