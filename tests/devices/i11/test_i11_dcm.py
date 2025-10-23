import bluesky.plans as bp
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_emitted,
    set_mock_value,
)

from dodal.devices.i11.dcm import DCM


@pytest.fixture
async def i11_dcm() -> DCM:
    async with init_devices(mock=True):
        i11_dcm = DCM(prefix="x-MO-DCM-01:", xtal_prefix="x-DI-DCM-01:")
    return i11_dcm


def test_count_i11_dcm(
    run_engine: RunEngine,
    run_engine_documents: dict[str, list[dict]],
    i11_dcm: DCM,
):
    run_engine(bp.count([i11_dcm]))
    assert_emitted(
        run_engine_documents,
        start=1,
        descriptor=1,
        event=1,
        stop=1,
    )


@pytest.mark.parametrize(
    "wavelength,energy,unit",
    [
        (0.0, 0.0, "angstrom"),
        (1.0, 12.3984, "angstrom"),
        (2.0, 6.1992, "angstrom"),
    ],
)
async def test_i11_wavelength(
    wavelength: float,
    energy: float,
    unit: str,
    i11_dcm: DCM,
):
    set_mock_value(i11_dcm.energy_in_kev.user_readback, energy)
    set_mock_value(i11_dcm.wavelength_in_a.user_readback, wavelength)

    reading = await i11_dcm.read()

    assert reading["i11_dcm-energy_in_kev"]["value"] == energy
    assert reading["i11_dcm-wavelength_in_a"]["value"] == wavelength
    assert reading["i11_dcm-wavelength"]["value"] == wavelength
