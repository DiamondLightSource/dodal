from unittest.mock import patch

import pytest
from ophyd_async.core import DetectorTrigger, DeviceCollector
from ophyd_async.epics.areadetector.controllers import (
    ADSimController,
)
from ophyd_async.epics.areadetector.drivers import ADBase
from ophyd_async.epics.areadetector.utils import ImageMode

from dodal.devices.areadetector.epics.drivers.pimte1_driver import Pimte1Driver
from dodal.devices.areadetector.epics.pimte_controller import PimteController


@pytest.fixture
async def pimte(RE) -> PimteController:
    async with DeviceCollector(sim=True):
        drv = Pimte1Driver("DRIVER:")
        controller = PimteController(drv)

    return controller


@pytest.fixture
async def ad(RE) -> ADSimController:
    async with DeviceCollector(sim=True):
        drv = ADBase("DRIVER:")
        controller = ADSimController(drv)

    return controller


async def test_pimte_controller(RE, pimte: PimteController):
    with patch("ophyd_async.core.signal.wait_for_value", return_value=None):
        await pimte.arm(num=1, exposure=0.002, trigger=DetectorTrigger.internal)

    driver = pimte.driver

    assert await driver.num_images.get_value() == 1
    assert await driver.image_mode.get_value() == ImageMode.multiple
    assert await driver.trigger_mode.get_value() == Pimte1Driver.TriggerMode.internal
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == 0.002
    assert pimte.get_deadtime(2) == 2 + 0.1

    with patch(
        "ophyd_async.epics.areadetector.utils.wait_for_value", return_value=None
    ):
        await pimte.disarm()
        await pimte.set_temperature(20)
        await pimte.set_speed(driver.SpeedMode.adc_200Khz)
    assert await driver.set_temperture.get_value() == 20
    assert await driver.speed.get_value() == driver.SpeedMode.adc_200Khz

    assert await driver.acquire.get_value() is False
