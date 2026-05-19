import pytest
from ophyd_async.core import (
    get_mock_put,
    init_devices,
)
from ophyd_async.epics.adaravis import AravisDriverIO
from ophyd_async.epics.adcore import ADImageMode
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.single_trigger_detector import SingleTriggerDetector


@pytest.fixture
def single_trigger_driver_and_detector() -> tuple[
    AravisDriverIO, SingleTriggerDetector
]:
    with init_devices(mock=True):
        driver = AravisDriverIO("", name="driver")
        detector = SingleTriggerDetector(driver, name="detector")

    return driver, detector


async def test_when_staged_then_image_mode_set_and_plugins_waited(
    single_trigger_driver_and_detector: tuple[AravisDriverIO, SingleTriggerDetector],
):
    driver, detector = single_trigger_driver_and_detector

    await detector.stage()

    get_mock_put(driver.image_mode).assert_called_once_with(ADImageMode.SINGLE)
    get_mock_put(driver.wait_for_plugins).assert_called_once_with(True)


async def test_when_triggered_then_acquire_set(
    single_trigger_driver_and_detector: tuple[AravisDriverIO, SingleTriggerDetector],
):
    driver, detector = single_trigger_driver_and_detector

    await detector.trigger()

    get_mock_put(driver.acquire).assert_called_once_with(True)


async def test_when_read_then_expected_readings_returned(
    single_trigger_driver_and_detector: tuple[AravisDriverIO, SingleTriggerDetector],
):
    _, detector = single_trigger_driver_and_detector

    await assert_reading(
        detector,
        {"detector-drv-array_counter": partial_reading(0)},
    )
