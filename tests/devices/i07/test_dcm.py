import pytest
from ophyd_async.core import init_devices

from dodal.devices.i07.dcm import DCM


@pytest.fixture
async def dcm() -> DCM:
    async with init_devices(mock=True):
        dcm = DCM("DCM-01", "DCM-01")
    return dcm


async def test_read_and_describe_includes(
    dcm: DCM,
):
    description = await dcm.describe()
    reading = await dcm.read()

    expected_keys: list[str] = [
        "bragg_in_degrees",
        "energy_in_kev",
        "offset_in_mm",
        "wavelength_in_a",
        "vertical_in_mm",
        "xtal1_temp",
        "xtal2_temp",
        "xtal1_holder_temp",
        "xtal2_holder_temp",
        "gap_motor",
        "white_beam_stop_temp",
    ]
    for key in expected_keys:
        assert f"{dcm.name}-{key}" in reading
        assert f"{dcm.name}-{key}" in description
