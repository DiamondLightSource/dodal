import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import get_mock_put

from dodal.devices.electron_analyser.abstract_analyser_controller import (
    AbstractAnalyserController,
)
from dodal.devices.electron_analyser.abstract_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs_analyser_controller import (
    SpecsAnalyserController,
)
from dodal.devices.electron_analyser.specs_region import SpecsSequence
from dodal.devices.electron_analyser.util import to_kinetic_energy
from dodal.devices.electron_analyser.vgscienta_analyser_controller import (
    VGScientaAnalyserController,
)
from dodal.devices.electron_analyser.vgscienta_region import VGScientaSequence
from dodal.plan_stubs.electron_analyser.configure_controller import configure_analyser
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SEQUENCE_REGION_NAMES,
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
)


@pytest.fixture(params=[VGScientaSequence, SpecsSequence])
def sequence_class(request: pytest.FixtureRequest) -> type[AbstractBaseSequence]:
    return request.param


@pytest.fixture
def sequence_file(sequence_class: type[AbstractBaseSequence]) -> str:
    if sequence_class == VGScientaSequence:
        return TEST_VGSCIENTA_SEQUENCE
    elif sequence_class == SpecsSequence:
        return TEST_SPECS_SEQUENCE
    raise Exception


@pytest.fixture
def analyser_type(
    sequence_class: type[AbstractBaseSequence],
) -> type[AbstractAnalyserController]:
    if sequence_class == VGScientaSequence:
        return VGScientaAnalyserController
    elif sequence_class == SpecsSequence:
        return SpecsAnalyserController
    raise Exception


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=["region"])
def test_analyser_to_kinetic_energy(
    sim_analyser: AbstractAnalyserController,
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
    sim_analyser: AbstractAnalyserController,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_analyser(sim_analyser, region, excitation_energy))

    get_mock_put(sim_analyser.acquisition_mode).assert_called_once_with(
        region.acquisition_mode, wait=True
    )
    get_mock_put(sim_analyser.lens_mode).assert_called_once_with(
        region.lens_mode, wait=True
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_analyser: AbstractAnalyserController,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_analyser(sim_analyser, region, excitation_energy))

    expected_low_e = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    expected_high_e = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )
    expected_pass_e = region.pass_energy

    get_mock_put(sim_analyser.low_energy).assert_called_once_with(
        expected_low_e, wait=True
    )
    get_mock_put(sim_analyser.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )
    get_mock_put(sim_analyser.pass_energy).assert_called_once_with(
        expected_pass_e, wait=True
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
def test_given_region_that_analyser_sets_channel_correctly(
    sim_analyser: AbstractAnalyserController,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_analyser(sim_analyser, region, excitation_energy))

    expected_slices = region.slices
    expected_iterations = region.iterations
    get_mock_put(sim_analyser.slices).assert_called_once_with(
        expected_slices, wait=True
    )
    get_mock_put(sim_analyser.iterations).assert_called_once_with(
        expected_iterations, wait=True
    )
