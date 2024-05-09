import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.undulator import Undulator

SIM_INSERTION_PREFIX = "SR03S"


@pytest.mark.s03
def test_undulator_connects():
    with DeviceCollector():
        undulator = Undulator(f"{SIM_INSERTION_PREFIX}-MO-SERVC-01:")  # noqa: F841
