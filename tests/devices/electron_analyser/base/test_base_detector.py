from unittest.mock import AsyncMock

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.testing import assert_value

from dodal.devices.electron_analyser.base import (
    AbstractBaseRegion,
    EnergyMode,
    GenericElectronAnalyserDetector,
    GenericSequence,
)
from tests.devices.electron_analyser.helper_util import (
    TEST_SEQUENCE_REGION_NAMES,
    get_test_sequence,
)


@pytest.fixture
def sequence(sim_detector: GenericElectronAnalyserDetector) -> GenericSequence:
    return get_test_sequence(type(sim_detector))


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_detector_binding_energy_axis(
    sim_detector: GenericElectronAnalyserDetector,
    region: AbstractBaseRegion,
    run_engine: RunEngine,
) -> None:
    run_engine(bps.mv(sim_detector, region))

    excitation_energy = (
        await sim_detector._region_logic.energy_source.energy.get_value()
    )
    driver = sim_detector._region_logic.driver

    # Check binding energy is correct
    is_region_binding = region.is_binding_energy()
    is_driver_binding = await driver.energy_mode.get_value() == EnergyMode.BINDING
    # Catch that driver correctly reflects what region energy mode is.
    assert is_region_binding == is_driver_binding
    energy_axis = await driver.energy_axis.get_value()
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_driver_binding else e for e in energy_axis]
    )
    await assert_value(sim_detector.binding_energy_axis, expected_binding_energy_axis)


def test_analyser_detector_loads_sequence_correctly(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
) -> None:
    seq = sim_detector.create_region_detector_list(sequence.get_enabled_regions())
    assert seq is not None


def test_analyser_detector_has_driver_as_child_and_region_detector_does_not(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
) -> None:
    # Remove parent name from driver name so it can be checked it exists in
    # _child_devices dict
    driver_name = sim_detector._region_logic.driver.name.replace(
        sim_detector.name + "-", ""
    )

    assert sim_detector._region_logic.driver.parent == sim_detector
    assert sim_detector._child_devices.get(driver_name) is not None

    region_detectors = sim_detector.create_region_detector_list(
        sequence.get_enabled_regions()
    )
    for det in region_detectors:
        assert det._child_devices.get(driver_name) is None
        assert det._region_logic.driver.parent == sim_detector


def test_analyser_detector_set_called_region_logic_setup_with_region(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
    run_engine: RunEngine,
) -> None:
    region = sequence.get_enabled_regions()[0]
    sim_detector._region_logic.setup_with_region = AsyncMock()
    run_engine(bps.mv(sim_detector, region), wait=True)
    sim_detector._region_logic.setup_with_region.assert_awaited_once_with(region)
