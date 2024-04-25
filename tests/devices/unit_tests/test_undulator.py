import pytest
from ophyd_async.core import (
    DeviceCollector,
)

from dodal.devices.undulator import Undulator


@pytest.fixture
async def undulator() -> Undulator:
    async with DeviceCollector(sim=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            lookup_table_path="./tests/devices/unit_tests/test_beamline_undulator_to_gap_lookup_table.txt",
        )
    return undulator


def test_lookup_table_path_passed(undulator: Undulator):
    assert (
        undulator.lookup_table_path
        == "./tests/devices/unit_tests/test_beamline_undulator_to_gap_lookup_table.txt"
    )


@pytest.mark.parametrize(
    "key",
    [
        "undulator-gap_motor",
        "undulator-current_gap",
        "undulator-gap_access",
    ],
)
async def test_read_and_describe_includes(
    undulator: Undulator,
    key: str,
):
    description = await undulator.describe()
    reading = await undulator.read()

    assert key in description
    assert key in reading
