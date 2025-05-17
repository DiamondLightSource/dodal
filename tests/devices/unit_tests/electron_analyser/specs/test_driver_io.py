from collections.abc import Sequence

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.plan_stubs import mv
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    get_mock_put,
    set_mock_value,
)

from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsDetector,
    SpecsRegionDetector,
)
from dodal.devices.electron_analyser.types import EnergyMode
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_SEQUENCE_REGION_NAMES,
    TEST_SPECS_SEQUENCE,
    assert_read_configuration_has_expected_value,
)


@pytest.fixture
def detector_class() -> type[SpecsDetector]:
    return SpecsDetector


@pytest.fixture
def region_detector_list(
    sim_detector: SpecsDetector,
) -> Sequence[SpecsRegionDetector]:
    return sim_detector.create_region_detector_list(
        TEST_SPECS_SEQUENCE, enabled_only=False
    )


@pytest.fixture
def region_detector(
    request: pytest.FixtureRequest,
    region_detector_list: Sequence[SpecsRegionDetector],
) -> SpecsRegionDetector:
    name = request.param
    region = next(
        (r_det for r_det in region_detector_list if r_det.region.name == name),
        None,
    )
    if region is None:
        raise ValueError("Region " + request.param + " is not found.")
    return region


@pytest.mark.parametrize("region_detector", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_energy_values_correctly(
    region_detector: SpecsRegionDetector,
    RE: RunEngine,
) -> None:
    RE(bps.stage(region_detector, wait=True))

    region = region_detector.region
    driver = region_detector.driver

    if region_detector.region.acquisition_mode == "Fixed Energy":
        get_mock_put(driver.energy_step).assert_called_once_with(
            region.energy_step, wait=True
        )
        await assert_read_configuration_has_expected_value(
            driver, "energy_step", region.energy_step
        )
    else:
        get_mock_put(driver.energy_step).assert_not_called()

    if region.acquisition_mode == "Fixed Transmission":
        get_mock_put(driver.centre_energy).assert_called_once_with(
            region.centre_energy, wait=True
        )
        await assert_read_configuration_has_expected_value(
            driver, "centre_energy", region.centre_energy
        )
    else:
        get_mock_put(driver.centre_energy).assert_not_called()


@pytest.mark.parametrize("region_detector", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_modes_correctly(
    region_detector: SpecsRegionDetector,
    RE: RunEngine,
) -> None:
    RE(bps.stage(region_detector, wait=True))

    region = region_detector.region
    driver = region_detector.driver

    get_mock_put(driver.psu_mode).assert_called_once_with(region.psu_mode, wait=True)
    await assert_read_configuration_has_expected_value(
        driver, "psu_mode", region.psu_mode
    )

    get_mock_put(driver.snapshot_values).assert_called_once_with(
        region.values, wait=True
    )
    await assert_read_configuration_has_expected_value(
        driver, "snapshot_values", region.values
    )


@pytest.mark.parametrize("region_detector", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_that_data_to_read_is_correct(
    region_detector: SpecsRegionDetector,
    excitation_energy: float,
    RE: RunEngine,
):
    RE(bps.stage(region_detector, wait=True))

    driver = region_detector.driver

    # Check binding energy is correct
    is_binding = await driver.energy_mode.get_value() == EnergyMode.BINDING
    energy_axis = await driver.energy_axis.get_value()
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_binding else e for e in energy_axis]
    )
    assert np.array_equal(
        await driver.binding_energy_axis.get_value(),
        expected_binding_energy_axis,
    )


@pytest.fixture
def driver_class() -> type[SpecsAnalyserDriverIO]:
    return SpecsAnalyserDriverIO


async def test_specs_analyser_energy_axis(
    sim_driver: SpecsAnalyserDriverIO,
    RE: RunEngine,
) -> None:
    start_energy = 1
    end_energy = 10
    total_points_iterations = 11

    RE(mv(sim_driver.low_energy, start_energy))
    RE(mv(sim_driver.high_energy, end_energy))
    RE(mv(sim_driver.slices, total_points_iterations))

    energy_axis = await sim_driver.energy_axis.get_value()
    expected_energy_axis = [1.0, 1.9, 2.8, 3.7, 4.6, 5.5, 6.4, 7.3, 8.2, 9.1, 10.0]
    np.testing.assert_array_equal(energy_axis, expected_energy_axis)


async def test_specs_analyser_angle_axis(
    sim_driver: SpecsAnalyserDriverIO,
    RE: RunEngine,
) -> None:
    max_angle = 21
    min_angle = 1
    slices = 10

    set_mock_value(sim_driver.min_angle_axis, min_angle)
    set_mock_value(sim_driver.max_angle_axis, max_angle)
    RE(mv(sim_driver.slices, slices))

    angle_axis = await sim_driver.angle_axis.get_value()
    expected_angle_axis = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    np.testing.assert_array_equal(angle_axis, expected_angle_axis)
