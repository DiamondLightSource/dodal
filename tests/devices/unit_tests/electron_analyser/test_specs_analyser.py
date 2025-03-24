import pytest
from bluesky.plan_stubs import abs_set
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    get_mock_put,
)

from dodal.devices.electron_analyser.specs_analyser import SpecsAnalyser
from dodal.devices.electron_analyser.specs_region import SpecsRegion, SpecsSequence


@pytest.fixture
def RE() -> RunEngine:
    return RunEngine()


@pytest.fixture
def analyser_type() -> type[SpecsAnalyser]:
    return SpecsAnalyser


@pytest.fixture
def sequence_file() -> str:
    return "specs_sequence.seq"


@pytest.fixture
def sequence_class() -> type[SpecsSequence]:
    return SpecsSequence


@pytest.fixture
def excitation_energy_eV() -> float:
    return 1000.0


@pytest.fixture
def region(request: pytest.FixtureRequest, sequence: SpecsSequence) -> SpecsRegion:
    region = sequence.get_region_by_name(request.param)
    if region is None:
        raise ValueError("Region " + request.param + " is not found.")
    return region


def region_names():
    return ["region", "region2"]


@pytest.mark.parametrize("region", region_names(), indirect=["region"])
def test_given_region_that_analyser_sets_modes_correctly(
    sim_analyser: SpecsAnalyser,
    region: SpecsRegion,
    excitation_energy_eV: float,
    RE: RunEngine,
) -> None:
    RE(abs_set(sim_analyser, region, excitation_energy_eV))

    get_mock_put(sim_analyser.acquisition_mode).assert_called_once_with(
        region.acquisitionMode, wait=True
    )
    get_mock_put(sim_analyser.lens_mode).assert_called_once_with(
        region.lensMode, wait=True
    )
    get_mock_put(sim_analyser.psu_mode).assert_called_once_with(
        region.psuMode, wait=True
    )


@pytest.mark.parametrize("region", region_names(), indirect=["region"])
def test_given_region_that__analyser_sets_energy_values_correctly(
    sim_analyser: SpecsAnalyser,
    region: SpecsRegion,
    excitation_energy_eV: float,
    RE: RunEngine,
) -> None:
    RE(abs_set(sim_analyser, region, excitation_energy_eV))

    expected_low_e = region.to_kinetic_energy(region.lowEnergy, excitation_energy_eV)
    expected_high_e = region.to_kinetic_energy(region.highEnergy, excitation_energy_eV)

    expected_step_e = region.get_energy_step_eV()
    expected_pass_e = (sim_analyser.get_pass_energy_type())(region.passEnergy)
    expected_values = region.values

    get_mock_put(sim_analyser.low_energy).assert_called_once_with(
        expected_low_e, wait=True
    )
    get_mock_put(sim_analyser.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )

    if region.acquisitionMode == "Fixed Energy":
        get_mock_put(sim_analyser.energy_step).assert_called_once_with(
            expected_step_e, wait=True
        )
    else:
        get_mock_put(sim_analyser.energy_step).assert_not_called()

    if region.acquisitionMode == "Fixed Transmission":
        get_mock_put(sim_analyser.centre_energy).assert_called_once_with(
            region.centreEnergy, wait=True
        )
    else:
        get_mock_put(sim_analyser.centre_energy).assert_not_called()

    get_mock_put(sim_analyser.pass_energy).assert_called_once_with(
        expected_pass_e, wait=True
    )

    get_mock_put(sim_analyser.values).assert_called_once_with(
        expected_values, wait=True
    )


@pytest.mark.parametrize("region", region_names(), indirect=["region"])
def test_given_region_that_analyser_sets_channel_correctly(
    region: SpecsRegion,
    sim_analyser: SpecsAnalyser,
    excitation_energy_eV: float,
    RE: RunEngine,
) -> None:
    RE(abs_set(sim_analyser, region, excitation_energy_eV))

    expected_slices = region.slices
    expected_iterations = region.iterations
    get_mock_put(sim_analyser.slices).assert_called_once_with(
        expected_slices, wait=True
    )
    get_mock_put(sim_analyser.iterations).assert_called_once_with(
        expected_iterations, wait=True
    )
