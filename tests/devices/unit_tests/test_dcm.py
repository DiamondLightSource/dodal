import pytest
from ophyd_async.core import (
    DeviceCollector,
)

from dodal.devices.dcm import DCM


@pytest.fixture
async def dcm() -> DCM:
    async with DeviceCollector(mock=True):
        dcm = DCM("DCM-01", name="dcm")
    return dcm


@pytest.mark.parametrize(
    "key",
    [
        "dcm-backplate_temp",
        "dcm-bragg_in_degrees",
        "dcm-energy_in_kev",
        "dcm-offset_in_mm",
    ],
)
async def test_read_and_describe_includes(
    dcm: DCM,
    key: str,
):
    description = await dcm.describe()
    reading = await dcm.read()

    assert key in description
    assert key in reading
