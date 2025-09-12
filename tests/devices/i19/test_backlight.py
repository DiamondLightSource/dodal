import pytest
from ophyd_async.core import InOut, init_devices

from dodal.devices.i19.backlight import BacklightPosition


@pytest.fixture
def fake_backlight():
    with init_devices(mock=True):
        backlight = BacklightPosition("test", "backlight")
    return backlight


async def test_backlight_set_position(fake_backlight):
    await fake_backlight.set(InOut.IN)
    assert await fake_backlight.position.get_value() == InOut.IN
    await fake_backlight.set(InOut.OUT)
    assert await fake_backlight.position.get_value() == InOut.OUT
