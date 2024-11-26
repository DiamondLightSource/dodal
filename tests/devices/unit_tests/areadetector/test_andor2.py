from collections import defaultdict
from pathlib import Path
from unittest.mock import Mock

import pytest
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DetectorTrigger,
    DeviceCollector,
    FilenameProvider,
    StaticFilenameProvider,
    StaticPathProvider,
    TriggerInfo,
    assert_emitted,
    callback_on_mock_put,
    set_mock_value,
)
from ophyd_async.epics.adcore._core_io import DetectorState

from dodal.devices.areadetector import Andor2
from dodal.devices.areadetector.andor2_epics import (
    Andor2DriverIO,
    Andor2TriggerMode,
    ImageMode,
)
from dodal.devices.areadetector.andor2_epics.andor2_controller import (
    DEFAULT_MAX_NUM_IMAGE,
    MIN_DEAD_TIME,
    Andor2Controller,
)


@pytest.fixture
def static_filename_provider():
    return StaticFilenameProvider("ophyd_async_tests")


@pytest.fixture
def static_path_provider_factory(tmp_path: Path):
    def create_static_dir_provider_given_fp(fp: FilenameProvider):
        return StaticPathProvider(fp, tmp_path)

    return create_static_dir_provider_given_fp


@pytest.fixture
def static_path_provider(
    static_path_provider_factory,
    static_filename_provider: FilenameProvider,
):
    return static_path_provider_factory(static_filename_provider)


@pytest.fixture
async def andor_controller() -> Andor2Controller:
    async with DeviceCollector(mock=True):
        drv = Andor2DriverIO("DRIVER:")
        andor_controller = Andor2Controller(drv)

    return andor_controller


async def test_andor_controller_prepare_and_arm_with_TriggerInfo(
    RE, andor_controller: Andor2Controller
):
    await andor_controller.prepare(
        trigger_info=TriggerInfo(number_of_triggers=1, livetime=0.002)
    )
    await andor_controller.arm()

    driver = andor_controller._drv
    assert await driver.num_images.get_value() == 1
    assert await driver.image_mode.get_value() == ImageMode.multiple
    assert await driver.trigger_mode.get_value() == Andor2TriggerMode.internal
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == 0.002


async def test_andor_controller_prepare_and_arm_with_no_livetime(
    RE, andor_controller: Andor2Controller
):
    # get driver and set the current acquire time.
    default_count_time = 2141
    driver = andor_controller._drv
    set_mock_value(driver.acquire_time, default_count_time)
    await andor_controller.prepare(trigger_info=TriggerInfo(number_of_triggers=5))
    await andor_controller.arm()

    assert await driver.num_images.get_value() == 5
    assert await driver.image_mode.get_value() == ImageMode.multiple
    assert await driver.trigger_mode.get_value() == Andor2TriggerMode.internal
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == default_count_time


async def test_andor_controller_prepare_and_arm_with_trigger_number_of_zero(
    RE, andor_controller: Andor2Controller
):
    # get driver and set the current acquire time.
    default_count_time = 1231
    driver = andor_controller._drv
    set_mock_value(driver.acquire_time, default_count_time)
    await andor_controller.prepare(trigger_info=TriggerInfo(number_of_triggers=0))
    await andor_controller.arm()

    assert await driver.num_images.get_value() == DEFAULT_MAX_NUM_IMAGE
    assert await driver.image_mode.get_value() == ImageMode.multiple
    assert await driver.trigger_mode.get_value() == Andor2TriggerMode.internal
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == default_count_time


async def test_andor_controller_disarm(RE, andor_controller: Andor2Controller):
    await andor_controller.disarm()
    driver = andor_controller._drv
    assert await driver.acquire.get_value() is False

    await andor_controller.disarm()


async def test_andor_incorrect_tigger_mode(RE, andor_controller: Andor2Controller):
    with pytest.raises(ValueError):
        andor_controller._get_trigger_mode(DetectorTrigger.variable_gate)

    assert await andor_controller._drv.acquire.get_value() is False


async def test_andor_controller_deadtime(RE, andor_controller: Andor2Controller):
    assert andor_controller.get_deadtime(2) == 2 + MIN_DEAD_TIME
    assert andor_controller.get_deadtime(None) == MIN_DEAD_TIME


@pytest.fixture
async def andor2(static_path_provider: StaticPathProvider) -> Andor2:
    async with DeviceCollector(mock=True):
        andor2 = Andor2("p99", static_path_provider, "andor2")

    set_mock_value(andor2._controller._drv.array_size_x, 10)
    set_mock_value(andor2._controller._drv.array_size_y, 20)
    set_mock_value(andor2.hdf.file_path_exists, True)
    set_mock_value(andor2.hdf.num_captured, 0)
    set_mock_value(andor2.hdf.file_path, str(static_path_provider._directory_path))
    set_mock_value(
        andor2.hdf.full_file_name,
        str(static_path_provider._directory_path) + "/test-andor2-hdf0",
    )

    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = range(0, 10000)
    callback_on_mock_put(
        andor2._writer.hdf.capture,
        lambda *_, **__: set_mock_value(andor2._writer.hdf.capture, value=True),
    )

    callback_on_mock_put(
        andor2.drv.acquire,
        lambda *_, **__: set_mock_value(
            andor2._writer.hdf.num_captured, rbv_mocks.get()
        ),
    )

    return andor2


async def test_andor2_RE(
    RE: RunEngine,
    andor2: Andor2,
    static_path_provider: StaticPathProvider,
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE.subscribe(capture_emitted)
    set_mock_value(andor2.drv.detector_state, DetectorState.Idle)
    RE(count([andor2], 10))
    assert (
        str(static_path_provider._directory_path)
        == await andor2.hdf.file_path.get_value()
    )
    assert (
        str(static_path_provider._directory_path) + "/test-andor2-hdf0"
        == await andor2.hdf.full_file_name.get_value()
    )
    assert_emitted(
        docs,
        start=1,
        descriptor=1,
        stream_resource=1,
        stream_datum=10,
        event=10,
        stop=1,
    )
