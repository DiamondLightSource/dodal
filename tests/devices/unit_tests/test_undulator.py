import pytest
from ophyd_async.core import (
    DeviceCollector,
)

from dodal.devices.undulator import Undulator


@pytest.fixture
async def undulator() -> Undulator:
    async with DeviceCollector(mock=True):
        undulator = Undulator("UND-01", 80, 2.0, name="undulator")
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


@pytest.mark.parametrize(
    "key",
    [
        "undulator-poles",
        "undulator-length",
    ],
)
async def test_read_and_describe_configuration_includes(
    undulator: Undulator,
    key: str,
):
    description = await undulator.describe_configuration()
    reading = await undulator.read_configuration()

    assert key in description
    assert key in reading
