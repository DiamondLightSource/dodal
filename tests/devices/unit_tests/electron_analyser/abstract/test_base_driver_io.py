import asyncio
import math
from collections.abc import Sequence

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.testing import get_mock_put, set_mock_value

from dodal.devices.electron_analyser import to_kinetic_energy
from dodal.devices.electron_analyser.abstract import (
    AbstractElectronAnalyserDetector,
    AbstractElectronAnalyserRegionDetector,
    ElectronAnalyserRegionDetector,
)
from dodal.devices.electron_analyser.specs import (
    SpecsDetector,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaDetector,
)
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_SEQUENCE_REGION_NAMES,
    assert_read_configuration_has_expected_value,
    assert_read_has_expected_value,
    get_test_sequence,
)


@pytest.fixture(params=[VGScientaDetector, SpecsDetector])
def detector_class(
    request: pytest.FixtureRequest,
) -> type[AbstractElectronAnalyserDetector]:
    return request.param


@pytest.fixture
def region_detector_list(
    sim_detector: SpecsDetector,
) -> Sequence[AbstractElectronAnalyserRegionDetector]:
    return sim_detector.create_region_detector_list(
        get_test_sequence(type(sim_detector)), enabled_only=False
    )


@pytest.fixture
def region_detector(
    request: pytest.FixtureRequest,
    region_detector_list: Sequence[AbstractElectronAnalyserRegionDetector],
) -> AbstractElectronAnalyserRegionDetector:
    name = request.param
    region = next(
        (r_det for r_det in region_detector_list if r_det.region.name == name),
        None,
    )
    if region is None:
        raise ValueError("Region " + request.param + " is not found.")
    return region


# ToDo - Need to remove excitation energy and be read in from device


@pytest.mark.parametrize("region_detector", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_modes_correctly(
    region_detector: ElectronAnalyserRegionDetector,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(bps.stage(region_detector, wait=True))

    region = region_detector.region
    driver = region_detector.driver

    get_mock_put(driver.region_name).assert_called_once_with(region.name, wait=True)
    await assert_read_configuration_has_expected_value(
        driver, "region_name", region.name
    )
    get_mock_put(driver.energy_mode).assert_called_once_with(
        region.energy_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        driver, "energy_mode", region.energy_mode
    )
    get_mock_put(driver.acquisition_mode).assert_called_once_with(
        region.acquisition_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        driver, "acquisition_mode", region.acquisition_mode
    )
    get_mock_put(driver.lens_mode).assert_called_once_with(region.lens_mode, wait=True)
    await assert_read_configuration_has_expected_value(
        driver, "lens_mode", region.lens_mode
    )


@pytest.mark.parametrize("region_detector", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_energy_values_correctly(
    region_detector: ElectronAnalyserRegionDetector,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(bps.stage(region_detector, wait=True))

    region = region_detector.region
    driver = region_detector.driver

    expected_low_e = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    expected_high_e = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )
    expected_pass_e_type = driver.pass_energy_type
    expected_pass_e = expected_pass_e_type(region.pass_energy)

    get_mock_put(driver.low_energy).assert_called_once_with(expected_low_e, wait=True)
    await assert_read_configuration_has_expected_value(
        driver, "low_energy", expected_low_e
    )
    get_mock_put(driver.high_energy).assert_called_once_with(expected_high_e, wait=True)
    await assert_read_configuration_has_expected_value(
        driver, "high_energy", expected_high_e
    )
    get_mock_put(driver.pass_energy).assert_called_once_with(expected_pass_e, wait=True)
    await assert_read_configuration_has_expected_value(
        driver, "pass_energy", expected_pass_e
    )

    get_mock_put(driver.excitation_energy).assert_called_once_with(
        excitation_energy, wait=True
    )
    await assert_read_has_expected_value(driver, "excitation_energy", excitation_energy)


@pytest.mark.parametrize("region_detector", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_channel_correctly(
    region_detector: ElectronAnalyserRegionDetector,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(bps.stage(region_detector, wait=True))

    region = region_detector.region
    driver = region_detector.driver

    expected_slices = region.slices
    expected_iterations = region.iterations
    get_mock_put(driver.slices).assert_called_once_with(expected_slices, wait=True)
    await assert_read_configuration_has_expected_value(
        driver, "slices", expected_slices
    )
    get_mock_put(driver.iterations).assert_called_once_with(
        expected_iterations, wait=True
    )
    await assert_read_configuration_has_expected_value(
        driver, "iterations", expected_iterations
    )


@pytest.mark.parametrize("region_detector", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_that_data_to_read_is_correct(
    region_detector: ElectronAnalyserRegionDetector,
    excitation_energy: float,
    RE: RunEngine,
):
    RE(bps.stage(region_detector, wait=True))

    driver = region_detector.driver

    expected_total_time = math.prod(
        await asyncio.gather(
            driver.iterations.get_value(),
            driver.total_steps.get_value(),
            driver.step_time.get_value(),
        )
    )
    assert await driver.total_time.get_value() == expected_total_time

    spectrum = np.array([1, 2, 3, 4, 5], dtype=float)
    expected_total_intensity = np.sum(spectrum)
    set_mock_value(driver.spectrum, spectrum)
    assert await driver.total_intensity.get_value() == expected_total_intensity
