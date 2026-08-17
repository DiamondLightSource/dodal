from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i06_1.magnet import (
    MagnetAxisPowerSupply,
    MagnetMode,
    MagnetPositionError,
    MagnetRequest,
    ThreeMagnetAxisPowerSupply,
)


@pytest.fixture
def axis_psu() -> MagnetAxisPowerSupply:
    with init_devices(mock=True):
        axis_psu = MagnetAxisPowerSupply("TEST:")
    return axis_psu


@pytest.fixture
def psu() -> ThreeMagnetAxisPowerSupply:
    with init_devices(mock=True):
        psu = ThreeMagnetAxisPowerSupply("TEST:")
    return psu


async def test_power_supply_axis_within_limit_does_not_raise(
    axis_psu: MagnetAxisPowerSupply,
) -> None:
    set_mock_value(axis_psu.limit, 2.0)

    await axis_psu.check_axis_with_limit(1.5, MagnetMode.UNIAXIAL_X, "x")


async def test_power_supply__axis_none_position_does_not_check_limit(
    axis_psu: MagnetAxisPowerSupply,
) -> None:
    set_mock_value(axis_psu.limit, 0.0)

    await axis_psu.check_axis_with_limit(None, MagnetMode.UNIAXIAL_X, "x")


async def test_power_supply__axis_outside_limit_raises(
    axis_psu: MagnetAxisPowerSupply,
) -> None:
    set_mock_value(axis_psu.limit, 2.0)

    with pytest.raises(
        MagnetPositionError,
        match=r"Axis x with value 3.0 exceeds limit 2.0T",
    ):
        await axis_psu.check_axis_with_limit(3.0, MagnetMode.UNIAXIAL_X, "x")


async def test_power_supply_axis_check_axes_within_limit_checks_each_axis(
    psu: ThreeMagnetAxisPowerSupply,
) -> None:
    psu.x.check_axis_with_limit = AsyncMock()
    psu.y.check_axis_with_limit = AsyncMock()
    psu.z.check_axis_with_limit = AsyncMock()

    request = MagnetRequest(x=1, y=2, z=3)
    await psu.check_axes_within_limit(request, MagnetMode.CUBIC)
    psu.x.check_axis_with_limit.assert_awaited_once_with(1, MagnetMode.CUBIC, "x")
    psu.y.check_axis_with_limit.assert_awaited_once_with(2, MagnetMode.CUBIC, "y")
    psu.z.check_axis_with_limit.assert_awaited_once_with(3, MagnetMode.CUBIC, "z")


async def test_power_supply_check_axes_within_limit_passes_none_values(
    psu: ThreeMagnetAxisPowerSupply,
) -> None:
    psu.x.check_axis_with_limit = AsyncMock()
    psu.y.check_axis_with_limit = AsyncMock()
    psu.z.check_axis_with_limit = AsyncMock()

    request = MagnetRequest(x=1, y=None, z=None)

    await psu.check_axes_within_limit(request, MagnetMode.UNIAXIAL_X)

    psu.x.check_axis_with_limit.assert_awaited_once_with(1, MagnetMode.UNIAXIAL_X, "x")
    psu.y.check_axis_with_limit.assert_awaited_once_with(
        None, MagnetMode.UNIAXIAL_X, "y"
    )
    psu.z.check_axis_with_limit.assert_awaited_once_with(
        None, MagnetMode.UNIAXIAL_X, "z"
    )


async def test_power_supply_read(psu: ThreeMagnetAxisPowerSupply):
    await assert_reading(
        psu,
        {
            "psu-x-limit": partial_reading(0),
            "psu-x-ramp_rate": partial_reading(0),
            "psu-y-limit": partial_reading(0),
            "psu-y-ramp_rate": partial_reading(0),
            "psu-z-limit": partial_reading(0),
            "psu-z-ramp_rate": partial_reading(0),
        },
    )
