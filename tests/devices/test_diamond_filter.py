from unittest.mock import ANY

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading

from dodal.devices.diamond_filter import DiamondFilter, I03Filters, I04Filters


@pytest.fixture
async def i03_diamond_filter() -> DiamondFilter[I03Filters]:
    async with init_devices(mock=True):
        i03_diamond_filter = DiamondFilter("", I03Filters, name="diamond_filter")
    return i03_diamond_filter


@pytest.fixture
async def i04_diamond_filter() -> DiamondFilter[I04Filters]:
    async with init_devices(mock=True):
        i04_diamond_filter = DiamondFilter("", I04Filters, name="diamond_filter")
    return i04_diamond_filter


async def test_reading_includes_read_fields(
    i03_diamond_filter: DiamondFilter[I03Filters],
):
    await assert_reading(
        i03_diamond_filter,
        {
            "diamond_filter-stage_position": {
                "value": I03Filters.EMPTY,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_i03_can_set_enums_as_expected(
    i03_diamond_filter: DiamondFilter[I03Filters],
):
    await i03_diamond_filter.stage_position.set(I03Filters.TWO_HUNDRED)
    assert (
        await i03_diamond_filter.stage_position.get_value()
    ) == I03Filters.TWO_HUNDRED


async def test_i04_can_set_enums_as_expected(
    i04_diamond_filter: DiamondFilter[I04Filters],
):
    await i04_diamond_filter.stage_position.set(I04Filters.FIFTY)
    assert (await i04_diamond_filter.stage_position.get_value()) == I04Filters.FIFTY
