import pytest
from ophyd_async.core import OnOff, init_devices

from dodal.devices.thawer import Thawer


@pytest.fixture
def thawer():
    with init_devices(mock=True):
        thawer = Thawer("", name="thawer")
    return thawer


async def test_when_thawer_stopped_then_stops_thawing(thawer: Thawer):
    await thawer.set(OnOff.ON)
    await thawer.stop()
    assert (await thawer._control.get_value()) == OnOff.OFF
