import re

import pytest
from bluesky.plan_stubs import mv
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_reading,
    partial_reading,
)

from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.i09_1_shared import (
    HardEnergy,
    HardInsertionDeviceEnergy,
    calculate_energy_i09_hu,
    calculate_gap_i09_hu,
    get_hu_lut_as_dict,
)
from dodal.devices.undulator import UndulatorInMm, UndulatorOrder
from tests.devices.i09_1_shared.test_data import TEST_HARD_UNDULATOR_LUT


@pytest.fixture
async def lut_dictionary() -> dict:
    return await get_hu_lut_as_dict(TEST_HARD_UNDULATOR_LUT)


@pytest.fixture
def undulator_order() -> UndulatorOrder:
    with init_devices(mock=True):
        undulator_order = UndulatorOrder()
    return undulator_order


@pytest.fixture
async def dcm() -> DoubleCrystalMonochromatorWithDSpacing:
    async with init_devices(mock=True):
        dcm = DoubleCrystalMonochromatorWithDSpacing(
            "TEST-MO-DCM-01:", PitchAndRollCrystal, StationaryCrystal
        )
    return dcm


@pytest.fixture
async def undulator_in_mm() -> UndulatorInMm:
    async with init_devices(mock=True):
        undulator_mm = UndulatorInMm("UND-02")
    return undulator_mm


@pytest.fixture
async def hu_id_energy(
    undulator_order: UndulatorOrder,
    undulator_in_mm: UndulatorInMm,
    lut_dictionary: dict,
) -> HardInsertionDeviceEnergy:
    async with init_devices():
        hu_id_energy = HardInsertionDeviceEnergy(
            undulator_order=undulator_order,
            undulator=undulator_in_mm,
            lut=lut_dictionary,
            gap_to_energy_func=calculate_energy_i09_hu,
            energy_to_gap_func=calculate_gap_i09_hu,
        )
    return hu_id_energy


@pytest.fixture
async def hu_energy(
    hu_id_energy: HardInsertionDeviceEnergy,
    dcm: DoubleCrystalMonochromatorWithDSpacing,
) -> HardEnergy:
    async with init_devices(mock=True):
        hu_energy = HardEnergy(
            dcm=dcm,
            undulator_energy=hu_id_energy,
        )
    return hu_energy


async def test_hu_id_energy_reading_includes_read_fields(
    run_engine: RunEngine,
    hu_id_energy: HardInsertionDeviceEnergy,
):
    # need to set correct order to avoid errors in reading
    await hu_id_energy._undulator_order_ref().value.set(3)
    energy_value = 3.1416
    run_engine(mv(hu_id_energy, energy_value))
    await assert_reading(
        hu_id_energy,
        {
            "hu_id_energy-energy": partial_reading(energy_value),
            "hu_id_energy-energy_demand": partial_reading(energy_value),
            "undulator_mm-current_gap": partial_reading(0.0),
            "undulator_order-value": partial_reading(3.0),
        },
    )


async def test_hu_id_energy_set_energy_fails(
    hu_id_energy: HardInsertionDeviceEnergy,
):
    value = 100.5
    with pytest.raises(
        ValueError,
        match=re.escape(f"Requested energy {value} keV is out of range for harmonic 3"),
    ):
        await hu_id_energy.set(value)


async def test_hu_id_energy_energy_demand_initialised_correctly(
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
        (2.130, 1, 12.814),
        (2.780, 3, 6.0531),
        (6.240, 5, 7.956),
    ],
)
async def test_hu_id_energy_set_energy_updates_gap(
    run_engine: RunEngine,
    hu_id_energy: HardInsertionDeviceEnergy,
    energy_value: float,
    order_value: int,
    expected_gap: float,
):
    await hu_id_energy._undulator_order_ref().value.set(order_value)
    assert await hu_id_energy._undulator_order_ref().value.get_value() == order_value
    run_engine(mv(hu_id_energy, energy_value))
    assert await hu_id_energy.energy_demand.get_value() == pytest.approx(
        energy_value, abs=0.001
    )
    assert await hu_id_energy.energy.get_value() == pytest.approx(
        energy_value, abs=0.001
    )
    assert (
        await hu_id_energy._undulator_ref().gap_motor.user_readback.get_value()
        == pytest.approx(expected_gap, abs=0.001)
    )


async def test_hu_energy_read_include_read_fields(
    hu_energy: HardEnergy,
    run_engine: RunEngine,
):
    await hu_energy._undulator_energy_ref()._undulator_order_ref().value.set(3)
    energy_value = 3.1416
    run_engine(mv(hu_energy, energy_value))
    await assert_reading(
        hu_energy,
        {
            "dcm-energy_in_keV": partial_reading(energy_value),
            "hu_id_energy-energy": partial_reading(energy_value),
            "hu_id_energy-energy_demand": partial_reading(energy_value),
            "undulator_mm-current_gap": partial_reading(0.0),
            "undulator_order-value": partial_reading(3.0),
        },
    )


async def test_hu_energy_set_both_dcm_and_id_energy(
    run_engine: RunEngine,
    hu_energy: HardEnergy,
):
    energy_value = 3.1415
    run_engine(mv(hu_energy, energy_value))
    assert (
        await hu_energy._undulator_energy_ref().energy_demand.get_value()
        == pytest.approx(energy_value, abs=0.00001)
    )
    assert (
        await hu_energy._dcm_ref().energy_in_keV.user_readback.get_value()
        == pytest.approx(energy_value, abs=0.00001)
    )


async def test_hu_energy_move_energy_fails(
    run_engine: RunEngine,
    hu_energy: HardEnergy,
):
    energy_value = 5.15
    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Requested energy {energy_value} keV is out of range for harmonic 3: [2.4, 4.3] keV"
        ),
    ):
        await hu_energy.set(energy_value)


@pytest.mark.parametrize(
    "energy_value, order_value, expected_gap",
    [
        (2.781, 3, 6.055),
        (6.241, 5, 7.957),
    ],
)
async def test_hu_energy_set_moves_gap(
    run_engine: RunEngine,
    hu_energy: HardEnergy,
    energy_value: float,
    order_value: int,
    expected_gap: float,
):
    await (
        hu_energy._undulator_energy_ref()._undulator_order_ref().value.set(order_value)
    )
    assert (
        await hu_energy._undulator_energy_ref()._undulator_order_ref().value.get_value()
        == pytest.approx(order_value, abs=0.00001)
    )
    run_engine(mv(hu_energy, energy_value))
    assert (
        await hu_energy._undulator_energy_ref()
        ._undulator_ref()
        .gap_motor.user_readback.get_value()
        == pytest.approx(expected_gap, abs=0.001)
    )


async def test_hu_energy_locate(
    run_engine: RunEngine,
    hu_energy: HardEnergy,
):
    energy_value = 3.1415
    run_engine(mv(hu_energy, energy_value))
    located_position = await hu_energy.locate()
    assert located_position == {"readback": energy_value, "setpoint": energy_value}
