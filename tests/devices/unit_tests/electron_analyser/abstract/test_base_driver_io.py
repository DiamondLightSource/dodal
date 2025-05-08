import asyncio
import math

import numpy as np
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import get_mock_put, set_mock_value

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser import to_kinetic_energy
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.vgscienta import VGScientaAnalyserDriverIO
from dodal.plan_stubs.electron_analyser import configure_analyser
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SEQUENCE_REGION_NAMES,
    assert_read_configuration_has_expected_value,
    assert_read_has_expected_value,
    get_test_sequence,
    get_test_sequence_type,
)


@pytest.fixture(params=[SpecsAnalyserDriverIO, VGScientaAnalyserDriverIO])
def driver_class(
    request: pytest.FixtureRequest,
) -> type[AbstractAnalyserDriverIO]:
    return request.param


@pytest.fixture
def sequence(
    driver_class: type[AbstractAnalyserDriverIO],
) -> AbstractBaseSequence[AbstractBaseRegion]:
    return load_json_file_to_class(
        get_test_sequence_type(driver_class), get_test_sequence(driver_class)
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=["region"])
def test_analyser_to_kinetic_energy(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
) -> None:
    low_energy = region.low_energy
    ke = to_kinetic_energy(low_energy, region.energy_mode, excitation_energy)
    if region.is_binding_energy():
        assert ke == (excitation_energy - low_energy)
    else:
        assert ke == low_energy


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_modes_correctly(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_analyser(sim_driver, region, excitation_energy))

    get_mock_put(sim_driver.region_name).assert_called_once_with(region.name, wait=True)
    await assert_read_configuration_has_expected_value(
        sim_driver, "region_name", region.name
    )
    get_mock_put(sim_driver.energy_mode).assert_called_once_with(
        region.energy_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "energy_mode", region.energy_mode
    )
    get_mock_put(sim_driver.acquisition_mode).assert_called_once_with(
        region.acquisition_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "acquisition_mode", region.acquisition_mode
    )
    get_mock_put(sim_driver.lens_mode).assert_called_once_with(
        region.lens_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "lens_mode", region.lens_mode
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_analyser(sim_driver, region, excitation_energy))

    expected_low_e = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    expected_high_e = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )
    expected_pass_e_type = sim_driver.pass_energy_type
    expected_pass_e = expected_pass_e_type(region.pass_energy)

    get_mock_put(sim_driver.low_energy).assert_called_once_with(
        expected_low_e, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "low_energy", expected_low_e
    )
    get_mock_put(sim_driver.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "high_energy", expected_high_e
    )
    get_mock_put(sim_driver.pass_energy).assert_called_once_with(
        expected_pass_e, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "pass_energy", expected_pass_e
    )

    get_mock_put(sim_driver.excitation_energy).assert_called_once_with(
        excitation_energy, wait=True
    )
    await assert_read_has_expected_value(
        sim_driver, "excitation_energy", excitation_energy
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_channel_correctly(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_analyser(sim_driver, region, excitation_energy))

    expected_slices = region.slices
    expected_iterations = region.iterations
    get_mock_put(sim_driver.slices).assert_called_once_with(expected_slices, wait=True)
    await assert_read_configuration_has_expected_value(
        sim_driver, "slices", expected_slices
    )
    get_mock_put(sim_driver.iterations).assert_called_once_with(
        expected_iterations, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "iterations", expected_iterations
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_that_data_to_read_is_correct(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
):
    RE(configure_analyser(sim_driver, region, excitation_energy))

    expected_total_time = math.prod(
        await asyncio.gather(
            sim_driver.iterations.get_value(),
            sim_driver.total_steps.get_value(),
            sim_driver.step_time.get_value(),
        )
    )
    assert await sim_driver.total_time.get_value() == expected_total_time

    spectrum = np.array([1, 2, 3, 4, 5], dtype=float)
    expected_total_intensity = np.sum(spectrum)
    set_mock_value(sim_driver.spectrum, spectrum)
    assert await sim_driver.total_intensity.get_value() == expected_total_intensity
