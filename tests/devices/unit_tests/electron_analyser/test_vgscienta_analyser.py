import pytest
from bluesky.plan_stubs import abs_set
from bluesky.run_engine import RunEngine
from ophyd_async.testing import get_mock_put

from dodal.devices.electron_analyser.vgscienta_analyser import VGScientaAnalyser
from dodal.devices.electron_analyser.vgscienta_region import (
    VGScientaRegion,
    VGScientaSequence,
)


@pytest.fixture
def RE() -> RunEngine:
    return RunEngine()


@pytest.fixture
def sequence_file() -> str:
    return "vgscienta_sequence.seq"


@pytest.fixture
def sequence_class() -> type[VGScientaSequence]:
    return VGScientaSequence


@pytest.fixture
def excitation_energy_eV() -> float:
    return 1000.0


@pytest.fixture
def analyser_type() -> type[VGScientaAnalyser]:
    return VGScientaAnalyser


@pytest.fixture
def region(
    request: pytest.FixtureRequest, sequence: VGScientaSequence
) -> VGScientaRegion:
    region = sequence.get_region_by_name(request.param)
    if region is None:
        raise ValueError("Region " + request.param + " is not found.")
    return region


def region_names():
    return ["New_Region", "New_Region1"]


@pytest.mark.parametrize("region", region_names(), indirect=["region"])
def test_given_region_that_analyser_sets_modes_correctly(
    sim_analyser: VGScientaAnalyser,
    region: VGScientaRegion,
    excitation_energy_eV: float,
    RE: RunEngine,
) -> None:
    RE(abs_set(sim_analyser, region, excitation_energy_eV))

    get_mock_put(sim_analyser.acquisition_mode).assert_called_once_with(
        region.acquisitionMode, wait=True
    )
    get_mock_put(sim_analyser.detector_mode).assert_called_once_with(
        region.detectorMode, wait=True
    )
    get_mock_put(sim_analyser.lens_mode).assert_called_once_with(
        region.lensMode, wait=True
    )
    get_mock_put(sim_analyser.image_mode).assert_called_once_with("Single", wait=True)


@pytest.mark.parametrize("region", region_names(), indirect=["region"])
def test_given_region_that__analyser_sets_energy_values_correctly(
    sim_analyser: VGScientaAnalyser,
    region: VGScientaRegion,
    excitation_energy_eV: float,
    RE: RunEngine,
) -> None:
    RE(abs_set(sim_analyser, region, excitation_energy_eV))

    expected_low_e = region.to_kinetic_energy(region.lowEnergy, excitation_energy_eV)
    expected_high_e = region.to_kinetic_energy(region.highEnergy, excitation_energy_eV)
    expected_centre_e = region.to_kinetic_energy(region.fixEnergy, excitation_energy_eV)
    expected_step_e = region.get_energy_step_eV()
    expected_pass_e = (sim_analyser.get_pass_energy_type())(region.passEnergy)

    get_mock_put(sim_analyser.low_energy).assert_called_once_with(
        expected_low_e, wait=True
    )
    get_mock_put(sim_analyser.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )
    get_mock_put(sim_analyser.centre_energy).assert_called_once_with(
        expected_centre_e, wait=True
    )
    get_mock_put(sim_analyser.energy_step).assert_called_once_with(
        expected_step_e, wait=True
    )
    get_mock_put(sim_analyser.pass_energy).assert_called_once_with(
        expected_pass_e, wait=True
    )


@pytest.mark.parametrize("region", region_names(), indirect=["region"])
def test_given_region_that_analyser_sets_channel_correctly(
    region: VGScientaRegion,
    sim_analyser: VGScientaAnalyser,
    excitation_energy_eV: float,
    RE: RunEngine,
) -> None:
    RE(abs_set(sim_analyser, region, excitation_energy_eV))

    expected_first_x = region.firstXChannel
    expected_size_x = region.x_channel_size()
    get_mock_put(sim_analyser.first_x_channel).assert_called_once_with(
        expected_first_x, wait=True
    )
    get_mock_put(sim_analyser.x_channel_size).assert_called_once_with(
        expected_size_x, wait=True
    )

    expected_first_y = region.firstYChannel
    expected_size_y = region.y_channel_size()
    get_mock_put(sim_analyser.first_y_channel).assert_called_once_with(
        expected_first_y, wait=True
    )
    get_mock_put(sim_analyser.y_channel_size).assert_called_once_with(
        expected_size_y, wait=True
    )

    expected_slices = region.slices
    expected_iterations = region.iterations
    get_mock_put(sim_analyser.slices).assert_called_once_with(
        expected_slices, wait=True
    )
    get_mock_put(sim_analyser.iterations).assert_called_once_with(
        expected_iterations, wait=True
    )
