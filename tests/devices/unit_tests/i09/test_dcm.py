import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_value,
    set_mock_value,
)

from dodal.devices.i09.dcm import DCM


@pytest.fixture
async def dcm() -> DCM:
    async with init_devices(mock=True):
        dcm = DCM("DCM-01", name="dcm")
    return dcm


@pytest.mark.parametrize(
    "energy_kev, energy_ev",
    [
        (0.0, 0.0),
        (1.0, 1000.0),
        (0.102, 102.0),
    ],
)
async def test_ev_to_kev(
    dcm: DCM,
    energy_kev: float,
    energy_ev: float,
):
    set_mock_value(dcm.energy_in_kev.user_readback, energy_kev)
    await assert_value(dcm.energy_in_ev, energy_ev)


@pytest.mark.parametrize(
    "key",
    [
        "dcm-bragg_in_degrees",
        "dcm-energy_in_kev",
        "dcm-energy_in_ev",
        "dcm-offset_in_mm",
        "dcm-wavelength_in_a",
        "dcm-xtal_1-roll_in_mrad",
        "dcm-xtal_1-pitch_in_mrad",
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
