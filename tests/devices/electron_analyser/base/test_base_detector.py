from unittest.mock import AsyncMock

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import TriggerInfo
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
)

from dodal.devices.electron_analyser.base import (
    GenericBaseElectronAnalyserDetector,
    GenericElectronAnalyserDetector,
    GenericSequence,
)
from tests.devices.electron_analyser.helper_util.sequence import get_test_sequence


@pytest.fixture
def sequence(sim_detector: GenericElectronAnalyserDetector) -> GenericSequence:
    return get_test_sequence(type(sim_detector))


def test_base_analyser_detector_trigger(
    sim_detector: GenericBaseElectronAnalyserDetector,
    run_engine: RunEngine,
) -> None:
    sim_detector._controller.arm = AsyncMock()
    sim_detector._controller.wait_for_idle = AsyncMock()

    run_engine(bps.trigger(sim_detector, wait=True), wait=True)

    sim_detector._controller.arm.assert_awaited_once()
    sim_detector._controller.wait_for_idle.assert_awaited_once()


async def test_base_analyser_detector_read(
    sim_detector: GenericBaseElectronAnalyserDetector,
) -> None:
    driver_read = await sim_detector._controller.driver.read()
    await assert_reading(sim_detector, driver_read)


async def test_base_analyser_describe(
    sim_detector: GenericBaseElectronAnalyserDetector,
) -> None:
    energy_array = await sim_detector._controller.driver.energy_axis.get_value()
    angle_array = await sim_detector._controller.driver.angle_axis.get_value()
    data = await sim_detector.describe()
    assert data[f"{sim_detector._controller.driver.image.name}"]["shape"] == [
        len(angle_array),
        len(energy_array),
    ]


async def test_base_analyser_detector_configuration(
    sim_detector: GenericBaseElectronAnalyserDetector,
) -> None:
    driver_config = await sim_detector._controller.driver.read_configuration()
    await assert_configuration(sim_detector, driver_config)


async def test_base_analyser_detector_describe_configuration(
    sim_detector: GenericBaseElectronAnalyserDetector,
) -> None:
    driver_describe_config = (
        await sim_detector._controller.driver.describe_configuration()
    )

    assert await sim_detector.describe_configuration() == driver_describe_config


def test_analyser_detector_loads_sequence_correctly(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
) -> None:
    seq = sim_detector.create_region_detector_list(sequence.get_enabled_regions())
    assert seq is not None


async def test_analyser_detector_stage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector._controller.disarm = AsyncMock()

    await sim_detector.stage()

    sim_detector._controller.disarm.assert_awaited_once()


async def test_analyser_detector_unstage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector._controller.disarm = AsyncMock()

    await sim_detector.unstage()

    sim_detector._controller.disarm.assert_awaited_once()


def test_analyser_detector_creates_region_detectors(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
) -> None:
    region_detectors = sim_detector.create_region_detector_list(
        sequence.get_enabled_regions()
    )
    assert len(region_detectors) == len(sequence.get_enabled_regions())
    for det in region_detectors:
        assert det.region.enabled is True
        assert det.name == sim_detector.name + "_" + det.region.name


def test_analyser_detector_has_driver_as_child_and_region_detector_does_not(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
) -> None:
    # Remove parent name from driver name so it can be checked it exists in
    # _child_devices dict
    driver_name = sim_detector._controller.driver.name.replace(
        sim_detector.name + "-", ""
    )

    assert sim_detector._controller.driver.parent == sim_detector
    assert sim_detector._child_devices.get(driver_name) is not None

    region_detectors = sim_detector.create_region_detector_list(
        sequence.get_enabled_regions()
    )
    for det in region_detectors:
        assert det._child_devices.get(driver_name) is None
        assert det._controller.driver.parent == sim_detector


def test_analyser_detector_trigger_called_controller_prepare(
    sim_detector: GenericElectronAnalyserDetector,
    run_engine: RunEngine,
) -> None:
    sim_detector._controller.prepare = AsyncMock()
    sim_detector._controller.arm = AsyncMock()
    sim_detector._controller.wait_for_idle = AsyncMock()

    run_engine(bps.trigger(sim_detector, wait=True), wait=True)

    sim_detector._controller.prepare.assert_awaited_once()
    sim_detector._controller.arm.assert_awaited_once()
    sim_detector._controller.wait_for_idle.assert_awaited_once()


def test_analyser_detector_set_called_controller_setup_with_region(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
    run_engine: RunEngine,
) -> None:
    region = sequence.get_enabled_regions()[0]
    sim_detector._controller.setup_with_region = AsyncMock()
    run_engine(bps.mv(sim_detector, region), wait=True)
    sim_detector._controller.setup_with_region.assert_awaited_once_with(region)


async def test_analyser_region_detector_trigger_sets_driver_with_region(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
    run_engine: RunEngine,
) -> None:
    region_detectors = sim_detector.create_region_detector_list(
        sequence.get_enabled_regions()
    )
    trigger_info = TriggerInfo()

    for reg_det in region_detectors:
        reg_det.set = AsyncMock()
        reg_det._controller.prepare = AsyncMock()
        reg_det._controller.arm = AsyncMock()
        reg_det._controller.wait_for_idle = AsyncMock()

        run_engine(bps.trigger(reg_det, wait=True), wait=True)

        reg_det.set.assert_awaited_once_with(reg_det.region)
        reg_det._controller.prepare.assert_awaited_once_with(trigger_info)
        reg_det._controller.arm.assert_awaited_once()
        reg_det._controller.wait_for_idle.assert_awaited_once()
