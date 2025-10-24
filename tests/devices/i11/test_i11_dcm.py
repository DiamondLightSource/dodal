import bluesky.plans as bp
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_emitted,
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
