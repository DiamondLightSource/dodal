import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import set_mock_value

from dodal.devices.i24.dual_backlight import BLPositions, DualBacklight, LedStatus


@pytest.fixture
async def fake_backlight() -> DualBacklight:
    RunEngine()
    fake_backlight = DualBacklight("", name="fake_backlight")
    await fake_backlight.connect(mock=True)
    return fake_backlight


async def test_dual_backlight_can_be_written_and_read_from(
    fake_backlight: DualBacklight,
    RE: RunEngine,
):
    RE(bps.abs_set(fake_backlight.led2, LedStatus.OFF, wait=True))
    assert await fake_backlight.led2.get_value() == "OFF"


async def test_backlight_position(
    fake_backlight: DualBacklight,
    RE: RunEngine,
):
    RE(bps.abs_set(fake_backlight.pos1.pos_level, BLPositions.IN, wait=True))
    assert await fake_backlight.pos1.pos_level.get_value() == "In"


async def test_when_led1_out_it_switches_off(
    fake_backlight: DualBacklight, RE: RunEngine
):
    set_mock_value(fake_backlight.led1, LedStatus.ON)
    RE(bps.abs_set(fake_backlight, BLPositions.OUT))
    assert await fake_backlight.pos1.pos_level.get_value() == "Out"
    assert await fake_backlight.led1.get_value() == "OFF"


async def test_when_led1_not_out_it_switches_on(
    fake_backlight: DualBacklight, RE: RunEngine
):
    RE(bps.abs_set(fake_backlight, "OAV2"))
    assert await fake_backlight.led1.get_value() == "ON"


async def test_led2_independent_from_led1_position(
    fake_backlight: DualBacklight, RE: RunEngine
):
    set_mock_value(fake_backlight.led2, LedStatus.OFF)
    RE(bps.abs_set(fake_backlight, BLPositions.IN, wait=True))
    assert await fake_backlight.led1.get_value() == "ON"
    assert await fake_backlight.led2.get_value() == "OFF"
