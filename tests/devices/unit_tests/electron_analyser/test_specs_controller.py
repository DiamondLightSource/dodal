import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    get_mock_put,
)

from dodal.devices.electron_analyser.specs_analyser_controller import (
    SpecsAnalyserController,
)
from dodal.devices.electron_analyser.specs_region import SpecsRegion, SpecsSequence
from dodal.plan_stubs.electron_analyser.configure_controller import configure_specs
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SEQUENCE_REGION_NAMES,
    TEST_SPECS_SEQUENCE,
)


@pytest.fixture
def analyser_type() -> type[SpecsAnalyserController]:
    return SpecsAnalyserController


@pytest.fixture
def sequence_file() -> str:
    return TEST_SPECS_SEQUENCE


@pytest.fixture
def sequence_class() -> type[SpecsSequence]:
    return SpecsSequence


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=["region"])
def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_analyser: SpecsAnalyserController,
    region: SpecsRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_specs(sim_analyser, region, excitation_energy))

    if region.acquisition_mode == "Fixed Energy":
        get_mock_put(sim_analyser.energy_step).assert_called_once_with(
            region.energy_step, wait=True
        )
    else:
        get_mock_put(sim_analyser.energy_step).assert_not_called()

    if region.acquisition_mode == "Fixed Transmission":
        get_mock_put(sim_analyser.centre_energy).assert_called_once_with(
            region.centre_energy, wait=True
        )
    else:
        get_mock_put(sim_analyser.centre_energy).assert_not_called()


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=["region"])
def test_given_region_that_analyser_sets_modes_correctly(
    sim_analyser: SpecsAnalyserController,
    region: SpecsRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_specs(sim_analyser, region, excitation_energy))

    get_mock_put(sim_analyser.psu_mode).assert_called_once_with(
        region.psu_mode, wait=True
    )
