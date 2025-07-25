from unittest.mock import AsyncMock

import pytest
from bluesky import plan_stubs as bps
from bluesky.protocols import Triggerable
from bluesky.run_engine import RunEngine
from ophyd_async.core import SignalR
from ophyd_async.epics.adcore import ADBaseController

import dodal.devices.b07 as b07
import dodal.devices.i09 as i09
from dodal.devices.electron_analyser import (
    GenericElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from tests.devices.unit_tests.electron_analyser.util import (
    create_analyser_device,
    get_test_sequence,
)


@pytest.fixture(
    params=[
        SpecsDetector[b07.LensMode, b07.PsuMode],
        VGScientaDetector[i09.LensMode, i09.PsuMode, i09.PassEnergy],
    ]
)
async def sim_detector(
    request: pytest.FixtureRequest, energy_sources: dict[str, SignalR[float]]
) -> GenericElectronAnalyserDetector:
    return await create_analyser_device(request.param, energy_sources)


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


def assert_detector_trigger_uses_controller_correctly(
    detector: Triggerable,
    controller: ADBaseController,
    RE: RunEngine,
) -> None:
    controller.arm = AsyncMock()
    controller.wait_for_idle = AsyncMock()

    RE(bps.trigger(detector), wait=True)

    controller.arm.assert_awaited_once()
    controller.wait_for_idle.assert_awaited_once()


def test_analyser_detector_trigger(
    sim_detector: GenericElectronAnalyserDetector,
    RE: RunEngine,
) -> None:
    assert_detector_trigger_uses_controller_correctly(
        sim_detector, sim_detector.controller, RE
    )


async def test_analyser_region_detector_trigger_sets_driver_with_region(
    sim_detector: GenericElectronAnalyserDetector,
    sequence_file_path: str,
    RE: RunEngine,
) -> None:
    region_detectors = sim_detector.create_region_detector_list(
        sequence_file_path, enabled_only=False
    )

    for reg_det in region_detectors:
        reg_det.driver.set = AsyncMock()

        assert_detector_trigger_uses_controller_correctly(
            reg_det, reg_det.controller, RE
        )

        reg_det.driver.set.assert_awaited_once_with(reg_det.region)


# ToDo - Add tests for BaseElectronAnalyserDetector class + controller
# ToDo - Add test that data being read is correct from plan
