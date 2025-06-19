from unittest.mock import AsyncMock

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.epics.motor import Motor

from dodal.devices.electron_analyser import GenericElectronAnalyserDetector
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from tests.devices.unit_tests.electron_analyser.util import get_test_sequence


@pytest.fixture(params=[SpecsDetector, VGScientaDetector])
def detector_class(
    request: pytest.FixtureRequest,
) -> type[GenericElectronAnalyserDetector]:
    return request.param


@pytest.fixture
def sequence_file_path(sim_detector: GenericElectronAnalyserDetector) -> str:
    return get_test_sequence(type(sim_detector))


def test_analyser_detector_loads_sequence_correctly(
    sim_detector: GenericElectronAnalyserDetector,
    sequence_file_path: str,
) -> None:
    seq = sim_detector.load_sequence(sequence_file_path)
    assert seq is not None


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
    driver_name = sim_detector.driver.name
    if sim_detector.name + "-" in driver_name:
        driver_name = driver_name.replace(sim_detector.name + "-", "")

    assert sim_detector.driver.parent == sim_detector
    assert sim_detector._child_devices.get(driver_name) is not None

    region_detectors = sim_detector.create_region_detector_list(sequence_file_path)

    for det in region_detectors:
        assert det._child_devices.get(driver_name) is None
        assert det.driver.parent == sim_detector


def test_analyser_region_detector_stage_prepares_driver_with_region(
    sim_detector: GenericElectronAnalyserDetector,
    sequence_file_path: str,
    sim_energy_source: Motor,
    RE: RunEngine,
) -> None:
    region_detectors = sim_detector.create_region_detector_list(
        sequence_file_path, enabled_only=False
    )

    for reg_det in region_detectors:
        reg_det.driver.prepare = AsyncMock()
        reg_det.driver.set = AsyncMock()

        RE(bps.prepare(reg_det, sim_energy_source, wait=True))
        reg_det.driver.prepare.assert_called_once_with(sim_energy_source)
        reg_det.driver.set.assert_called_once_with(reg_det.region)


# ToDo - Add tests for BaseElectronAnalyserDetector class + controller
# ToDo - Add test that data being read is correct from plan
