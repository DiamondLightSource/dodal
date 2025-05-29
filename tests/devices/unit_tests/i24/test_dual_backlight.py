import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.testing import set_mock_value

from dodal.devices.i24.dual_backlight import (
    BacklightPositions,
    DualBacklight,
    LEDStatus,
)


@pytest.fixture
async def fake_backlight(RE) -> DualBacklight:
    fake_backlight = DualBacklight("", name="fake_backlight")
    await fake_backlight.connect(mock=True)
    return fake_backlight


async def test_dual_backlight_can_be_written_and_read_from(
    fake_backlight: DualBacklight,
    RE: RunEngine,
):
    RE(bps.abs_set(fake_backlight.frontlight_state, LEDStatus.OFF, wait=True))
    assert await fake_backlight.frontlight_state.get_value() == "OFF"


async def test_backlight_position(
    fake_backlight: DualBacklight,
    RE: RunEngine,
):
    RE(
        bps.abs_set(
            fake_backlight.backlight_position.pos_level,
            BacklightPositions.IN,
            wait=True,
        )
    )
    assert await fake_backlight.backlight_position.pos_level.get_value() == "In"


async def test_when_backlight_out_it_switches_off(
    fake_backlight: DualBacklight, RE: RunEngine
):
    set_mock_value(fake_backlight.backlight_state, LEDStatus.ON)
    RE(bps.abs_set(fake_backlight, BacklightPositions.OUT, wait=True))
    assert await fake_backlight.backlight_position.pos_level.get_value() == "Out"
    assert await fake_backlight.backlight_state.get_value() == "OFF"


async def test_when_backlight_not_out_it_switches_on(
    fake_backlight: DualBacklight, RE: RunEngine
):
    RE(bps.abs_set(fake_backlight, "OAV2", wait=True))
    assert await fake_backlight.backlight_state.get_value() == "ON"


async def test_frontlight_independent_from_backlight_position(
    fake_backlight: DualBacklight, RE: RunEngine
):
    set_mock_value(fake_backlight.frontlight_state, LEDStatus.OFF)
    RE(bps.abs_set(fake_backlight, BacklightPositions.IN, wait=True))
    assert await fake_backlight.backlight_state.get_value() == "ON"
    assert await fake_backlight.frontlight_state.get_value() == "OFF"
