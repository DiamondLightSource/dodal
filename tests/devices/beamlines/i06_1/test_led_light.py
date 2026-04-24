import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.common.enums import OnOffUpper
from dodal.devices.beamlines.i06_1 import LEDLight


@pytest.fixture
def led_light() -> LEDLight:
    with init_devices(mock=True):
        led_light = LEDLight("TEST:")
    return led_light


async def test_led_light_read(led_light: LEDLight) -> None:
    await assert_reading(
        led_light,
        {
            "led_light-intensity": partial_reading(0),
            "led_light-switch": partial_reading(OnOffUpper.ON),
        },
    )
