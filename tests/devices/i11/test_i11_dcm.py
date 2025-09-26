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
    RE: RunEngine,
    run_engine_documents: dict[str, list[dict]],
    i11_dcm: DCM,
):
    RE(bp.count([i11_dcm]))
    assert_emitted(
        run_engine_documents,
        start=1,
        descriptor=1,
        event=1,
        stop=1,
    )


@pytest.mark.parametrize(
    "wavelength,energy",
    [
        (0.0, 0.0),
        (1.0, 12.3984),
        (2.0, 6.1992),
    ],
)
async def test_i11_wavelength(
    wavelength: float,
    energy: float,
    i11_dcm: DCM,
):
    set_mock_value(i11_dcm.energy_in_kev.user_readback, energy)
    reading = await i11_dcm.read()

    print(reading)

    assert reading["i11_dcm-energy_in_kev"]["value"] == energy
    assert reading["i11_dcm-wavelength"]["value"] == wavelength
