import pytest
from ophyd_async.core import (
    DeviceCollector,
)

from dodal.devices.undulator import Undulator


@pytest.fixture
async def undulator() -> Undulator:
    async with DeviceCollector(sim=True):
        undulator = Undulator("UND-01", name="undulator")
    return undulator


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
