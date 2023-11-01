from unittest.mock import patch

import pytest
from ophyd_async.core import DetectorTrigger, DeviceCollector
from ophyd_async.epics.areadetector.utils import ImageMode

from dodal.devices.areadetector.adaravis import (
    AdAravisMakoController,
    AdAravisMakoDriver,
    TriggerModeMako,
    TriggerSourceMako,
)


@pytest.fixture
async def ad_aravis(RE) -> AdAravisMakoController:
    async with DeviceCollector(sim=True):
        drv = AdAravisMakoDriver("DRIVER:")
        controller = AdAravisMakoController(drv, 1)

    return controller


async def test_ad_aravis_controller(RE, ad_aravis: AdAravisMakoController):
    with patch("ophyd_async.core.signal.wait_for_value", return_value=None):
        await ad_aravis.arm(mode=DetectorTrigger.constant_gate)

    driver = ad_aravis.driver
    assert await driver.num_images.get_value() == 0
    assert await driver.image_mode.get_value() == ImageMode.multiple
    assert await driver.trigger_mode.get_value() == TriggerModeMako.on
    assert await driver.trigger_source.get_value() == TriggerSourceMako.line_1
    assert await driver.acquire.get_value() is True

    with patch(
        "ophyd_async.epics.areadetector.utils.wait_for_value", return_value=None
    ):
        await ad_aravis.disarm()

    assert await driver.acquire.get_value() is False
