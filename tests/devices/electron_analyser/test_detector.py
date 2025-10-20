from unittest.mock import AsyncMock

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices

import dodal.devices.b07 as b07
import dodal.devices.i09 as i09
from dodal.devices.electron_analyser import (
    EnergySource,
    GenericElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.testing.electron_analyser import create_detector
from tests.devices.electron_analyser.helper_util import get_test_sequence


@pytest.fixture(
    params=[
        SpecsDetector[b07.LensMode, b07.PsuMode],
        VGScientaDetector[i09.LensMode, i09.PsuMode, i09.PassEnergy],
    ]
)
async def sim_detector(
    request: pytest.FixtureRequest,
    single_energy_source: EnergySource,
    RE: RunEngine,
) -> GenericElectronAnalyserDetector:
    async with init_devices(mock=True):
        sim_detector = await create_detector(
            request.param,
            prefix="TEST:",
            energy_source=single_energy_source,
        )
    return sim_detector


@pytest.fixture
def sequence_file_path(
    sim_detector: GenericElectronAnalyserDetector,
) -> str:
    return get_test_sequence(type(sim_detector))


def test_analyser_detector_loads_sequence_correctly(
    sim_detector: GenericElectronAnalyserDetector,
    sequence_file_path: str,
) -> None:
    seq = sim_detector.load_sequence(sequence_file_path)
    assert seq is not None


async def test_analyser_detector_stage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector._controller.disarm = AsyncMock()
    sim_detector.driver.stage = AsyncMock()

    await sim_detector.stage()

    sim_detector._controller.disarm.assert_awaited_once()
    sim_detector.driver.stage.assert_awaited_once()


async def test_analyser_detector_unstage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector._controller.disarm = AsyncMock()
    sim_detector.driver.unstage = AsyncMock()

    await sim_detector.unstage()

    sim_detector._controller.disarm.assert_awaited_once()
    sim_detector.driver.unstage.assert_awaited_once()


def test_analyser_detector_creates_region_detectors(
    sim_detector: GenericElectronAnalyserDetector,
    sequence_file_path: str,
) -> None:
    seq = sim_detector.load_sequence(sequence_file_path)
    region_detectors = sim_detector.create_region_detector_list(sequence_file_path)

    assert len(region_detectors) == len(seq.get_enabled_regions())
    for det in region_detectors:
        assert det.region.enabled is True
        assert det.name == sim_detector.name + "_" + det.region.name


def test_analyser_detector_has_driver_as_child_and_region_detector_does_not(
    sim_detector: GenericElectronAnalyserDetector,
    sequence_file_path: str,
) -> None:
    # Remove parent name from driver name so it can be checked it exists in
    # _child_devices dict
    driver_name = sim_detector.driver.name.replace(sim_detector.name + "-", "")

    assert sim_detector.driver.parent == sim_detector
    assert sim_detector._child_devices.get(driver_name) is not None

    region_detectors = sim_detector.create_region_detector_list(sequence_file_path)

    for det in region_detectors:
        assert det._child_devices.get(driver_name) is None
        assert det._controller.driver.parent == sim_detector


async def test_analyser_region_detector_trigger_sets_driver_with_region(
    sim_detector: GenericElectronAnalyserDetector,
    sequence_file_path: str,
    RE: RunEngine,
) -> None:
    region_detectors = sim_detector.create_region_detector_list(
        sequence_file_path, enabled_only=False
    )

    for reg_det in region_detectors:
        reg_det._controller.driver.set = AsyncMock()

        reg_det._controller.arm = AsyncMock()
        reg_det._controller.wait_for_idle = AsyncMock()

        RE(bps.trigger(reg_det), wait=True)

        reg_det._controller.arm.assert_awaited_once()
        reg_det._controller.wait_for_idle.assert_awaited_once()
        reg_det._controller.driver.set.assert_awaited_once_with(reg_det.region)
