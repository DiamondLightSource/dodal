import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i21 import I21SampleManipulatorStage


@pytest.fixture
def smp() -> I21SampleManipulatorStage:
    with init_devices(mock=True):
        smp = I21SampleManipulatorStage("TEST:")
    return smp


async def test_smp_read(smp: I21SampleManipulatorStage) -> None:
    await assert_reading(
        smp,
        {
            smp.x.name: partial_reading(0),
            smp.y.name: partial_reading(0),
            smp.z.name: partial_reading(0),
            smp.azimuth.name: partial_reading(0),
            smp.tilt.name: partial_reading(0),
            smp.polar.name: partial_reading(0),
            smp.difftth.name: partial_reading(0),
            smp.para.name: partial_reading(0),
            smp.perp.name: partial_reading(0),
        },
    )
