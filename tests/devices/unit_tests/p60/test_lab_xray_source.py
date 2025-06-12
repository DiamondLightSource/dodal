import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_value,
)

from dodal.devices.p60.lab_xray_source import LabXraySource, LabXraySourceReadable


@pytest.fixture
async def al_kalpha_source() -> LabXraySourceReadable:
    async with init_devices():
        al_kalpha_source = LabXraySourceReadable(LabXraySource.AL_KALPHA)
    return al_kalpha_source


@pytest.fixture
async def mg_kalpha_source() -> LabXraySourceReadable:
    async with init_devices():
        mg_kalpha_source = LabXraySourceReadable(LabXraySource.MG_KALPHA)
    return mg_kalpha_source


async def test_source_energy_correct(
    al_kalpha_source: LabXraySourceReadable,
    mg_kalpha_source: LabXraySourceReadable,
):
    await assert_value(
        al_kalpha_source.user_readback, float(LabXraySource.AL_KALPHA.value)
    )
    await assert_value(
        mg_kalpha_source.user_readback, float(LabXraySource.MG_KALPHA.value)
    )


async def test_read_empty(
    al_kalpha_source: LabXraySourceReadable,
    mg_kalpha_source: LabXraySourceReadable,
):
    readingAl = await al_kalpha_source.read()
    readingMg = await mg_kalpha_source.read()

    assert readingAl == {}
    assert readingMg == {}
