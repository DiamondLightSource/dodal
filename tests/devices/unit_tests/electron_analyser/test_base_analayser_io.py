import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import get_mock_put

from dodal.devices.electron_analyser.abstract_analyser_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs_analyser_io import (
    SpecsAnalyserDriverIO,
)
from dodal.devices.electron_analyser.specs_region import SpecsSequence
from dodal.devices.electron_analyser.vgscienta_analyser_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta_region import VGScientaSequence
from dodal.plan_stubs.electron_analyser.configure_controller import configure_analyser
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SEQUENCE_REGION_NAMES,
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
    assert_reading_has_expected_value,
)


@pytest.fixture(params=[SpecsSequence, VGScientaSequence])
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
) -> type[AbstractAnalyserDriverIO]:
    if sequence_class == VGScientaSequence:
        return VGScientaAnalyserDriverIO
    elif sequence_class == SpecsSequence:
        return SpecsAnalyserDriverIO
    raise Exception


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=["region"])
def test_analyser_to_kinetic_energy(
    sim_analyser_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
) -> None:
    low_energy = region.low_energy
    ke = sim_analyser_driver.to_kinetic_energy(
        low_energy, excitation_energy, region.energy_mode
    )
    if region.is_binding_energy():
        assert ke == (excitation_energy - low_energy)
    else:
        assert ke == low_energy


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_modes_correctly(
    sim_analyser_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_analyser(sim_analyser_driver, region, excitation_energy))

    get_mock_put(sim_analyser_driver.acquisition_mode).assert_called_once_with(
        region.acquisition_mode, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "acquisition_mode", region.acquisition_mode
    )
    get_mock_put(sim_analyser_driver.lens_mode).assert_called_once_with(
        region.lens_mode, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "lens_mode", region.lens_mode
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_analyser_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_analyser(sim_analyser_driver, region, excitation_energy))

    expected_low_e = region.to_kinetic_energy(region.low_energy, excitation_energy)
    expected_high_e = region.to_kinetic_energy(region.high_energy, excitation_energy)
    expected_pass_e_type = sim_analyser_driver.pass_energy_type
    expected_pass_e = expected_pass_e_type(region.pass_energy)

    get_mock_put(sim_analyser_driver.low_energy).assert_called_once_with(
        expected_low_e, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "low_energy", expected_low_e
    )
    get_mock_put(sim_analyser_driver.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "high_energy", expected_high_e
    )
    get_mock_put(sim_analyser_driver.pass_energy).assert_called_once_with(
        expected_pass_e, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "pass_energy", expected_pass_e
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_channel_correctly(
    sim_analyser_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_analyser(sim_analyser_driver, region, excitation_energy))

    expected_slices = region.slices
    expected_iterations = region.iterations
    get_mock_put(sim_analyser_driver.slices).assert_called_once_with(
        expected_slices, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "slices", expected_slices
    )
    get_mock_put(sim_analyser_driver.iterations).assert_called_once_with(
        expected_iterations, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "iterations", expected_iterations
    )
