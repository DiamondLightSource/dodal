import re
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from bluesky.plan_stubs import mv
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.i09_1_shared import HardUndulator, UndulatorOrder, calculate_gap_hu
from dodal.testing.setup import patch_all_motors
from tests.devices.i09_1_shared.test_data import TEST_HARD_UNDULATOR_LUT


@pytest.fixture
async def undulator_order() -> UndulatorOrder:
    async with init_devices(mock=True):
        order = UndulatorOrder(
            id_gap_lookup_table_path=TEST_HARD_UNDULATOR_LUT,
        )
    return order


@pytest.fixture
async def hu(
    undulator_order: UndulatorOrder,
) -> HardUndulator:
    async with init_devices(mock=True):
        hu = HardUndulator(
            prefix="HU-01",
            id_gap_lookup_table_path=TEST_HARD_UNDULATOR_LUT,
            calculate_gap_function=calculate_gap_hu,
            order=undulator_order,
        )
    patch_all_motors(hu)
    return hu


async def test_hard_undulator_read(
    hu: HardUndulator,
):
    await assert_reading(
        hu,
        {
            "hu-undulator_period": partial_reading(27),
            "hu-gap_offset": partial_reading(0.0),
            "hu-gap_access": partial_reading(EnabledDisabledUpper.ENABLED),
            "hu-current_gap": partial_reading(0.0),
            "hu-gap_motor": partial_reading(0.0),
            "order-_order": partial_reading(3),
        },
    )


async def test_check_energy_limits_throw_error(
    hu: HardUndulator,
    undulator_order: UndulatorOrder,
    RE: RunEngine,
):
    RE(mv(undulator_order, 5))
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Energy 3.0keV is out of range for order 5: (4.0-7.2 keV)\n Valid orders for this energy are: [1, 3]"
        ),
    ):
        await hu.set(3.0)


async def test_move_order(
    undulator_order: UndulatorOrder,
    RE: RunEngine,
):
    assert (await undulator_order.locate())["readback"] == 3  # default order
    RE(mv(undulator_order, 5))
    assert (await undulator_order.locate())["readback"] == 5  # no error
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Order 0 not found in lookup table, must be in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]"
        ),
    ):
        await undulator_order.set(0)


@patch("dodal.devices.i09_1_shared.hard_undulator.energy_distance_table")
async def test_update_cached_lookup_table_fails(
    mock_table: MagicMock,
    hu: HardUndulator,
):
    mock_table.return_value = np.empty(0)
    with pytest.raises(
        RuntimeError,
        match=re.escape("Failed to load lookup table from path"),
    ):
        await hu.set(1.0)


async def test_get_gap_for_energy_fails(
    hu: HardUndulator,
    undulator_order: UndulatorOrder,
):
    await undulator_order.set(1)
    hu._check_energy_limits = AsyncMock()
    with pytest.raises(
        ValueError,
        match=re.escape("diffraction parameter squared must be positive"),
    ):
        await hu.set(30.0)


@pytest.mark.parametrize(
    "energy, order, expected_gap",
    [
        (2.13, 1, 12.81),
        (2.78, 3, 6.05),
        (6.24, 5, 7.95),
    ],
)
async def test_move_undulator(
    hu: HardUndulator,
    undulator_order: UndulatorOrder,
    RE: RunEngine,
    energy: float,
    order: int,
    expected_gap: float,
):
    await undulator_order.set(order)
    RE(mv(hu, energy))
    assert await hu.gap_motor.user_readback.get_value() == pytest.approx(
        expected_gap, abs=0.01
    )
