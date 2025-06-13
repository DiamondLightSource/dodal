import pytest
from ophyd_async.core import (
    init_devices,
)

from dodal.devices.i03.dcm import DCM


@pytest.fixture
async def dcm() -> DCM:
    async with init_devices(mock=True):
        dcm = DCM("DCM-01", name="dcm")
    return dcm


async def test_metadata_reflection(dcm: DCM):
    signal = dcm.crystal_metadata_reflection
    v = await signal.read()
    assert v is not None, "Value is not clear"


@pytest.mark.parametrize(
    "key",
    [
        "dcm-backplate_temp",
        "dcm-bragg_in_degrees",
        "dcm-energy_in_kev",
        "dcm-offset_in_mm",
        "dcm-crystal_metadata_usage",
        "dcm-crystal_metadata_type",
        "dcm-crystal_metadata_reflection",
        "dcm-crystal_metadata_d_spacing_a",
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
