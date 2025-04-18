import numpy as np
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    get_mock_put,
)

from dodal.devices.electron_analyser.abstract_analyser_io import EnergyMode
from dodal.devices.electron_analyser.specs_analyser_io import (
    SpecsAnalyserDriverIO,
)
from dodal.devices.electron_analyser.specs_region import SpecsRegion, SpecsSequence
from dodal.plan_stubs.electron_analyser.configure_driver import configure_specs
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SEQUENCE_REGION_NAMES,
    TEST_SPECS_SEQUENCE,
    assert_reading_has_expected_value,
)


@pytest.fixture
def analyser_type() -> type[SpecsAnalyserDriverIO]:
    return SpecsAnalyserDriverIO


@pytest.fixture
def sequence_file() -> str:
    return TEST_SPECS_SEQUENCE


@pytest.fixture
def sequence_class() -> type[SpecsSequence]:
    return SpecsSequence


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=["region"])
async def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_analyser_driver: SpecsAnalyserDriverIO,
    region: SpecsRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_specs(sim_analyser_driver, region, excitation_energy))

    if region.acquisition_mode == "Fixed Energy":
        get_mock_put(sim_analyser_driver.energy_step).assert_called_once_with(
            region.energy_step, wait=True
        )
        await assert_reading_has_expected_value(
            sim_analyser_driver, "energy_step", region.energy_step
        )
    else:
        get_mock_put(sim_analyser_driver.energy_step).assert_not_called()

    if region.acquisition_mode == "Fixed Transmission":
        get_mock_put(sim_analyser_driver.centre_energy).assert_called_once_with(
            region.centre_energy, wait=True
        )
        await assert_reading_has_expected_value(
            sim_analyser_driver, "centre_energy", region.centre_energy
        )
    else:
        get_mock_put(sim_analyser_driver.centre_energy).assert_not_called()


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=["region"])
async def test_given_region_that_analyser_sets_modes_correctly(
    sim_analyser_driver: SpecsAnalyserDriverIO,
    region: SpecsRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_specs(sim_analyser_driver, region, excitation_energy))

    get_mock_put(sim_analyser_driver.psu_mode).assert_called_once_with(
        region.psu_mode, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "psu_mode", region.psu_mode
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_that_data_to_read_is_correct(
    sim_analyser_driver: SpecsAnalyserDriverIO,
    region: SpecsRegion,
    excitation_energy: float,
    RE: RunEngine,
):
    RE(configure_specs(sim_analyser_driver, region, excitation_energy))

    # Check binding energy is correct
    is_binding = await sim_analyser_driver.energy_mode.get_value() == EnergyMode.BINDING
    energy_axis = await sim_analyser_driver.energy_axis.get_value()
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_binding else e for e in energy_axis]
    )
    assert np.array_equal(
        await sim_analyser_driver.binding_energy_axis.get_value(),
        expected_binding_energy_axis,
    )
