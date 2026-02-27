import pytest
from ophyd_async.core import init_devices

from dodal.devices.beamlines.i21 import I21SampleManipulatorStage


@pytest.fixture
def smp() -> I21SampleManipulatorStage:
    with init_devices(mock=True):
        smp = I21SampleManipulatorStage("TEST:")
    return smp


def test_smp_read(smp: I21SampleManipulatorStage) -> None:
    pass
