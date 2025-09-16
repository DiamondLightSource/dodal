import pytest
from ophyd_async.core import init_devices

from dodal.common.enums import InOutUpper
from dodal.devices.i19.backlight import BacklightPosition


@pytest.fixture
async def fake_backlight():
    async with init_devices(mock=True):
        backlight = BacklightPosition("test", "backlight")
    return backlight


@pytest.mark.parametrize("position", [InOutUpper.IN, InOutUpper.OUT])
async def test_backlight_set_position(fake_backlight, position):
    await fake_backlight.set(position)
    assert await fake_backlight.position.get_value() == position
