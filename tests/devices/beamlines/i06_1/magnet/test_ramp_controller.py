import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i06_1.magnet import (
    MagnetAxisRampRateController,
    MagnetThreeAxesRampRateController,
)


@pytest.fixture
def magx_ramp_rate() -> MagnetAxisRampRateController:
    with init_devices(mock=True):
        magx_ramp_rate = MagnetAxisRampRateController("TEST:")
    return magx_ramp_rate


async def test_magx_ramp_rate_read(
    magx_ramp_rate: MagnetAxisRampRateController,
) -> None:
    await assert_reading(magx_ramp_rate, {"magx_ramp_rate": partial_reading(0)})


async def test_magx_ramp_rate_set(
    magx_ramp_rate: MagnetAxisRampRateController,
) -> None:
    ramp_rate = 1
    await magx_ramp_rate.set(ramp_rate)
    assert await magx_ramp_rate.readback.get_value() == ramp_rate


async def test_magx_ramp_rate_set_above_limit_throws_error(
    magx_ramp_rate: MagnetAxisRampRateController,
) -> None:
    ramp_rate = 10
    with pytest.raises(
        ValueError,
        match=f"Requested ramp rate {ramp_rate} exceeds the maximum limit of 2.0 for device {magx_ramp_rate.name}.",
    ):
        await magx_ramp_rate.set(ramp_rate)


@pytest.fixture
def mag_three_axis_ramp_rate() -> MagnetThreeAxesRampRateController:
    with init_devices(mock=True):
        mag_three_axis_ramp_rate = MagnetThreeAxesRampRateController("TEST:")
    return mag_three_axis_ramp_rate


async def test_mag_three_axis_ramp_rate_read(
    mag_three_axis_ramp_rate: MagnetThreeAxesRampRateController,
) -> None:
    await assert_reading(
        mag_three_axis_ramp_rate,
        {
            "mag_three_axis_ramp_rate-x": partial_reading(0),
            "mag_three_axis_ramp_rate-y": partial_reading(0),
            "mag_three_axis_ramp_rate-z": partial_reading(0),
        },
    )
