from unittest.mock import ANY, AsyncMock, patch

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, assert_reading, set_mock_value

from dodal.devices.backlight import Backlight, BacklightPosition, BacklightPower


@pytest.fixture
def fake_backlight(RE: RunEngine):
    with DeviceCollector(mock=True):
        backlight = Backlight("", "backlight")
    return backlight


async def test_backlight_can_be_written_and_read_from(fake_backlight: Backlight):
    set_mock_value(fake_backlight.position, BacklightPosition.IN)
    set_mock_value(fake_backlight.power, BacklightPower.ON)
    await assert_reading(
        fake_backlight,
        {
            "backlight-power": {
                "value": BacklightPower.ON,
                "alarm_severity": 0,
                "timestamp": ANY,
            },
            "backlight-position": {
                "value": BacklightPosition.IN,
                "alarm_severity": 0,
                "timestamp": ANY,
            },
        },
    )


@patch("dodal.devices.backlight.sleep", autospec=True)
async def test_when_backlight_moved_out_it_switches_off(
    mock_sleep: AsyncMock, fake_backlight: Backlight, RE: RunEngine
):
    RE(bps.mv(fake_backlight, BacklightPosition.OUT))  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    assert await fake_backlight.position.get_value() == BacklightPosition.OUT
    assert await fake_backlight.power.get_value() == BacklightPower.OFF


@patch("dodal.devices.backlight.sleep", autospec=True)
async def test_when_backlight_moved_in_it_switches_on(
    mock_sleep, fake_backlight: Backlight, RE: RunEngine
):
    RE(bps.mv(fake_backlight, BacklightPosition.IN))  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    assert await fake_backlight.position.get_value() == BacklightPosition.IN
    assert await fake_backlight.power.get_value() == BacklightPower.ON


@patch("dodal.devices.backlight.sleep", autospec=True)
async def test_given_backlight_in_when_backlight_moved_in_it_does_not_sleep(
    mock_sleep: AsyncMock, fake_backlight: Backlight, RE: RunEngine
):
    set_mock_value(fake_backlight.position, BacklightPosition.IN)
    RE(bps.mv(fake_backlight, BacklightPosition.IN))  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    mock_sleep.assert_not_awaited()


@patch("dodal.devices.backlight.sleep", autospec=True)
async def test_given_backlight_out_when_backlight_moved_in_it_sleeps(
    mock_sleep: AsyncMock, fake_backlight: Backlight, RE: RunEngine
):
    set_mock_value(fake_backlight.position, BacklightPosition.OUT)
    RE(bps.mv(fake_backlight, BacklightPosition.IN))  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
    mock_sleep.assert_awaited_once()
