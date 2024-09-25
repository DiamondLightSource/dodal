from collections import defaultdict
from pathlib import Path
from unittest.mock import Mock, patch

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
from dodal.devices.areadetector.andor2_epics.andor2_controller import Andor2Controller


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
async def Andor() -> Andor2Controller:
    async with DeviceCollector(mock=True):
        drv = Andor2DriverIO("DRIVER:")
        controller = Andor2Controller(drv)

    return controller


async def test_Andor_controller(RE, Andor: Andor2Controller):
    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.prepare(trigger_info=TriggerInfo(number=1, livetime=0.002))
        await Andor.arm()

    driver = Andor._drv

    set_mock_value(driver.accumulate_period, 1)
    assert await driver.num_images.get_value() == 1
    assert await driver.image_mode.get_value() == ImageMode.multiple
    assert await driver.trigger_mode.get_value() == Andor2TriggerMode.internal
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == 0.002
    assert Andor.get_deadtime(2) == 2 + 0.1
    assert Andor.get_deadtime(None) == 0.1

    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.disarm()

    assert await driver.acquire.get_value() is False

    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.disarm()
    with pytest.raises(ValueError):
        Andor._get_trigger_mode(DetectorTrigger.edge_trigger)

    assert await driver.acquire.get_value() is False


# area detector that is use for testing
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


async def test_Andor2_RE(
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
