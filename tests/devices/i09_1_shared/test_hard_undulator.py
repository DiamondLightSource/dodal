import re

import pytest
from bluesky.plan_stubs import mv
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.i09_1_shared import (
    HardUndulator,
    UndulatorOrder,
    calculate_gap_hu,
    get_hu_lut_as_dict,
)
from dodal.testing.setup import patch_all_motors
from tests.devices.i09_1_shared.test_data import TEST_HARD_UNDULATOR_LUT


@pytest.fixture
async def lut_dictionary() -> dict:
    return await get_hu_lut_as_dict(TEST_HARD_UNDULATOR_LUT)


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
            order=undulator_order,
            undulator_period=27,
            poles=4,
            length=100,
        )
    patch_all_motors(hu)
    return hu


async def test_undulator_config_default_parameters(
    undulator_order: UndulatorOrder,
):
    async with init_devices(mock=True):
        hu_default = HardUndulator(
            prefix="HU-01",
            order=undulator_order,
        )
    patch_all_motors(hu_default)
    await assert_configuration(
        hu_default,
        {
            "hu_default-gap_discrepancy_tolerance_mm": partial_reading(0.002),
            "hu_default-gap_motor-motor_egu": partial_reading(""),
            "hu_default-gap_motor-offset": partial_reading(0.0),
            "hu_default-gap_motor-velocity": partial_reading(3.0),
        },
    )


async def test_hard_undulator_read(
    hu: HardUndulator,
):
    await assert_reading(
        hu,
        {
            "hu-gap_offset": partial_reading(0.0),
            "hu-gap_access": partial_reading(EnabledDisabledUpper.ENABLED),
            "hu-current_gap": partial_reading(0.0),
            "hu-gap_motor": partial_reading(0.0),
            "order-_order": partial_reading(3),
        },
    )


async def test_hard_undulator_config(
    hu: HardUndulator,
):
    await assert_configuration(
        hu,
        {
            "hu-gap_discrepancy_tolerance_mm": partial_reading(0.002),
            "hu-gap_motor-motor_egu": partial_reading(""),
            "hu-gap_motor-offset": partial_reading(0.0),
            "hu-gap_motor-velocity": partial_reading(3.0),
            "hu-undulator_period": partial_reading(27.0),
            "hu-poles": partial_reading(4.0),
            "hu-length": partial_reading(100.0),
        },
    )


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


@pytest.mark.parametrize(
    "gap, order, expected_gap",
    [
        (12.81, 1, 12.81),
        (6.05, 3, 6.05),
        (6.04, 3, 6.04),
    ],
)
async def test_move_undulator(
    hu: HardUndulator,
    undulator_order: UndulatorOrder,
    RE: RunEngine,
    gap: float,
    order: int,
    expected_gap: float,
):
    await undulator_order.set(order)
    RE(mv(hu, gap))
    assert await hu.gap_motor.user_readback.get_value() == pytest.approx(
        expected_gap, abs=0.01
    )


@pytest.mark.parametrize(
    "energy, order, expected_gap",
    [
        (2.13, 1, 12.81),
        (2.78, 3, 6.05),
        (6.24, 5, 7.95),
    ],
)
async def test_calculate_gap_from_energy(
    energy: float,
    order: int,
    expected_gap: float,
    lut_dictionary: dict,
):
    assert calculate_gap_hu(energy, lut_dictionary, order) == pytest.approx(
        expected_gap, abs=0.01
    )


async def test_calculate_gap_from_energy_wrong_order(
    lut_dictionary: dict,
):
    wrong_order = 100
    with pytest.raises(
        ValueError,
        match=re.escape(f"Order parameter {wrong_order} not found in lookup table"),
    ):
        calculate_gap_hu(30, lut_dictionary, wrong_order)


async def test_calculate_gap_from_energy_wrong_k(
    lut_dictionary: dict,
):
    with pytest.raises(
        ValueError,
        match=re.escape("diffraction parameter squared must be positive!"),
    ):
        calculate_gap_hu(30, lut_dictionary, 1)
