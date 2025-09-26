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
async def dcm() -> DCM:
    async with init_devices(mock=True):
        dcm = DCM(prefix="x-MO-DCM-01:", xtal_prefix="x-DI-DCM-01:")
    return dcm


def test_count_dcm(
    RE: RunEngine,
    run_engine_documents: dict[str, list[dict]],
    dcm: DCM,
):
    RE(bp.count([dcm]))
    assert_emitted(
        run_engine_documents,
        start=1,
        descriptor=1,
        event=1,
        stop=1,
    )


@pytest.mark.parametrize(
    "energy,wavelength",
    [
        (0.0, 0.0),
        (1.0, 12.3984),
        (2.0, 6.1992),
    ],
)
async def test_wavelength(
    dcm: DCM,
    energy: float,
    wavelength: float,
):
    set_mock_value(dcm.energy_in_kev.user_readback, energy)
    reading = await dcm.read()

    assert reading["dcm-wavelength"]["value"] == wavelength
