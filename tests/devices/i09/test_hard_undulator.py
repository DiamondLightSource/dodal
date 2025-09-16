import pytest
from ophyd_async.core import init_devices

from dodal.devices.i09_shared.hard_undulator import HardUndulator
from dodal.testing.setup import patch_all_motors

LUT_TEST_PATH = "tests/devices/test_data/test_hard_undulator_lookup_table.txt"


@pytest.fixture
async def hu() -> HardUndulator:
    async with init_devices(mock=True):
        hu = HardUndulator(prefix="HU-01", id_gap_lookup_table_path=LUT_TEST_PATH)
    patch_all_motors(hu)
    return hu


async def test_read_and_describe_includes(
    hu: HardUndulator,
):
    description = await hu.describe()
    reading = await hu.read()

    expected_keys: list[str] = [
        "undulator_period",
        "gap_offset",
        "gap_access",
        "current_gap",
        "gap_motor",
        "order",
    ]
    for key in expected_keys:
        assert f"{hu.name}-{key}" in reading
        assert f"{hu.name}-{key}" in description


async def test_min_max_energy_for_order(
    hu: HardUndulator,
):
    min, max = await hu.get_min_max_energy_for_order(3)
    assert min == pytest.approx(2.4)
    assert max == pytest.approx(4.3)
    with pytest.raises(ValueError) as e:
        await hu.get_min_max_energy_for_order(0)
    assert (
        str(e.value)
        == "Order 0 not found in lookup table, must be between 1.0 and 23.0"
    )


async def test_check_energy_limits(
    hu: HardUndulator,
):
    await hu.check_energy_limits(3.0, 3)  # within limits
    with pytest.raises(ValueError) as e:
        await hu.check_energy_limits(1.0, 3)
    assert str(e.value) == "Energy 1.0keV is out of range for order 3: (2.4-4.3 keV)"
