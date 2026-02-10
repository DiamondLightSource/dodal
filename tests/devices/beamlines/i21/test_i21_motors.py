import pytest
from ophyd_async.core import init_devices

from dodal.devices.beamlines.i21 import XYZAzimuthTiltPolarParallelPerpendicularStage


@pytest.fixture
def smp() -> XYZAzimuthTiltPolarParallelPerpendicularStage:
    with init_devices(mock=True):
        smp = XYZAzimuthTiltPolarParallelPerpendicularStage("TEST:")
    return smp


def test_smp_read(smp: XYZAzimuthTiltPolarParallelPerpendicularStage) -> None:
    pass
