import pytest
from ophyd_async.core import init_devices

from dodal.devices.i09_shared.hard_undulator import HardUndulator

LUT_TEST_PATH = "tests/devices/test_data/test_hard_undulator_lookup_table.txt"


@pytest.fixture
async def hu() -> HardUndulator:
    async with init_devices(mock=True):
        hu = HardUndulator(prefix="HU-01", id_gap_lookup_table_path=LUT_TEST_PATH)
    return hu


async def test_read_and_describe_includes(
    hu: HardUndulator,
):
    description = await hu.describe()
    reading = await hu.read()

    expected_keys: list[str] = [
        "undulator_period",
        "gap_offset",
        "order_signal",
        "gap_access",
        "current_gap",
        "gap_motor",
    ]
    for key in expected_keys:
        assert f"{hu.name}-{key}" in reading
        assert f"{hu.name}-{key}" in description
