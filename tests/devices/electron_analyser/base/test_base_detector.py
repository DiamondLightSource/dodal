from unittest.mock import AsyncMock

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import TriggerInfo, init_devices, set_mock_value
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
)

from dodal.devices.beamlines.b07.analyser import Specs2DCMOS
from dodal.devices.beamlines.i09.analyser import EW4000
from dodal.devices.electron_analyser.base import (
    DualEnergySource,
    EnergySource,
    GenericAnalyserDriverIO,
    GenericBaseElectronAnalyserDetector,
    GenericElectronAnalyserDetector,
    GenericSequence,
)
from dodal.devices.electron_analyser.base.energy_sources import EnergySource
from dodal.devices.fast_shutter import DualFastShutter
from dodal.devices.selectable_source import SourceSelector


@pytest.fixture
def ew4000(
    dual_energy_source: DualEnergySource,
    dual_fast_shutter: DualFastShutter,
    source_selector: SourceSelector,
) -> EW4000:
    with init_devices(mock=True):
        ew4000 = EW4000("TEST:", dual_energy_source, dual_fast_shutter, source_selector)
    return ew4000


@pytest.fixture
def specs_2dcmos(single_energy_source: EnergySource) -> Specs2DCMOS:
    with init_devices(mock=True):
        specs_2dcmos = Specs2DCMOS("TEST:", single_energy_source)
    # Needed for specs so we don't get division by zero error.
    set_mock_value(specs_2dcmos.driver.slices, 1)
    return specs_2dcmos


@pytest.fixture(params=["ew4000", "specs_2dcmos"])
def sim_detector(
    request: pytest.FixtureRequest, ew4000: EW4000, specs_2dcmos: Specs2DCMOS
) -> GenericElectronAnalyserDetector:
    detectors = [ew4000, specs_2dcmos]
    for detector in detectors:
        if detector.name == request.param:
            return detector

    raise ValueError(f"Detector with name '{request.param}' not found")


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


@pytest.fixture
def sim_driver(
    sim_detector: GenericElectronAnalyserDetector,
) -> GenericAnalyserDriverIO:
    return sim_detector.driver


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
    region_detectors = sim_detector.create_region_detector_list(sequence.regions)

    assert len(region_detectors) == len(sequence.regions)
    for det in region_detectors:
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

    region_detectors = sim_detector.create_region_detector_list(sequence.regions)

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
    region_detectors = sim_detector.create_region_detector_list(sequence.regions)
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
