import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.undulator import Undulator

SIM_INSERTION_PREFIX = "SR03S"


@pytest.fixture
async def undulator() -> Undulator:
    with DeviceCollector():
        undulator = Undulator(f"{SIM_INSERTION_PREFIX}-MO-SERVC-01:")
    return undulator


@pytest.mark.s03
def test_undulator_connects(undulator: Undulator):
    ...
