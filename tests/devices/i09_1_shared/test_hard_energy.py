import re

import pytest
from bluesky.plan_stubs import mv
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_reading,
    partial_reading,
    set_mock_value,
)

from dodal.devices.i09_1_shared import (
    HardInsertionDeviceEnergy,
    calculate_gap_i09_hu,
    get_hu_lut_as_dict,
)
from dodal.devices.undulator import UndulatorInMm, UndulatorOrder
from dodal.testing.setup import patch_all_motors
from tests.devices.i09_1_shared.test_data import TEST_HARD_UNDULATOR_LUT


@pytest.fixture
async def lut_dictionary() -> dict:
    return await get_hu_lut_as_dict(TEST_HARD_UNDULATOR_LUT)


@pytest.fixture
def undulator_order() -> UndulatorOrder:
    with init_devices(mock=True):
        order = UndulatorOrder(name="undulator_order")
    set_mock_value(order.value, 3)
    return order


@pytest.fixture
async def undulator_in_mm() -> UndulatorInMm:
    async with init_devices(mock=True):
        undulator_mm = UndulatorInMm("UND-02")
    patch_all_motors(undulator_mm)
    return undulator_mm


@pytest.fixture
async def hu_id_energy(
    undulator_order: UndulatorOrder,
    undulator_in_mm: UndulatorInMm,
    lut_dictionary: dict,
) -> HardInsertionDeviceEnergy:
    hu = HardInsertionDeviceEnergy(
        undulator_order=undulator_order,
        undulator=undulator_in_mm,
        lut=lut_dictionary,  # Placeholder, will be set later_
        gap_to_energy_func=lambda gap,
        look_up_table,
        order: gap,  # Placeholder, not used in this context
        energy_to_gap_func=calculate_gap_i09_hu,
        name="hu_id_energy",
    )
    # patch_all_motors(hu)
    return hu


async def test_reading_includes_read_fields(hu_id_energy: HardInsertionDeviceEnergy):
    await assert_reading(
        hu_id_energy,
        {
            "hu_id_energy-energy": partial_reading(0.0),
            "hu_id_energy-energy_demand": partial_reading(0.0),
            "undulator_mm-current_gap": partial_reading(0.0),
            "undulator_order-value": partial_reading(3.0),
        },
    )


async def test_set_energy_fails(
    hu_id_energy: HardInsertionDeviceEnergy,
):
    value = 100.5
    with pytest.raises(
        ValueError,
        match=re.escape(f"Requested energy {value} keV is out of range for harmonic 3"),
    ):
        await hu_id_energy.set(value)


async def test_energy_demand_initialised_correctly(
    hu_id_energy: HardInsertionDeviceEnergy,
    run_engine: RunEngine,
):
    value = 3.456
    run_engine(mv(hu_id_energy, value))
    assert await hu_id_energy.energy_demand.get_value() == pytest.approx(
        value, abs=0.001
    )


@pytest.mark.parametrize(
    "energy_value, order_value, expected_gap",
    [
        (2.13, 1, 12.814),
        (2.78, 3, 6.053),
        (6.24, 5, 7.956),
    ],
)
async def test_set_energy_updates_gap(
    run_engine: RunEngine,
    hu_id_energy: HardInsertionDeviceEnergy,
    energy_value: float,
    order_value: int,
    expected_gap: float,
):
    await hu_id_energy._undulator_order().value.set(order_value)
    assert await hu_id_energy._undulator_order().value.get_value() == order_value
    run_engine(mv(hu_id_energy, energy_value))
    assert await hu_id_energy.energy_demand.get_value() == pytest.approx(
        energy_value, abs=0.001
    )
    assert (
        await hu_id_energy._undulator().gap_motor.user_readback.get_value()
        == pytest.approx(expected_gap, abs=0.001)
    )
