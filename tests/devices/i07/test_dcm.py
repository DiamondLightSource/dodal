import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i07.dcm import DCM


@pytest.fixture
async def dcm() -> DCM:
    async with init_devices(mock=True):
        dcm = DCM("DCM-01", "DCM-01")
    return dcm


async def test_dcm_read(
    dcm: DCM,
):
    await assert_reading(
        dcm,
        {
            f"{dcm.name}-bragg_in_degrees": partial_reading(0.0),
            f"{dcm.name}-energy_in_keV": partial_reading(0.0),
            f"{dcm.name}-energy_in_eV": partial_reading(0.0),
            f"{dcm.name}-offset_in_mm": partial_reading(0.0),
            f"{dcm.name}-wavelength_in_a": partial_reading(0.0),
            f"{dcm.name}-vertical_in_mm": partial_reading(0.0),
            f"{dcm.name}-xtal1_temp": partial_reading(0.0),
            f"{dcm.name}-xtal2_temp": partial_reading(0.0),
            f"{dcm.name}-xtal1_holder_temp": partial_reading(0.0),
            f"{dcm.name}-xtal2_holder_temp": partial_reading(0.0),
            f"{dcm.name}-xtal_1-pitch_in_mrad": partial_reading(0.0),
            f"{dcm.name}-xtal_1-roll_in_mrad": partial_reading(0.0),
            f"{dcm.name}-gap_motor": partial_reading(0.0),
            f"{dcm.name}-white_beam_stop_temp": partial_reading(0.0),
        },
    )
