import os

import pytest
from bluesky.plan_stubs import abs_set
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    get_mock_put,
)
from tests.devices.unit_tests.electron_analyser.test_utils import TEST_DATA_PATH

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.vgscienta_analyser import VGScientaAnalyser
from dodal.devices.electron_analyser.vgscienta_region import (
    VGScientaRegion,
    VGScientaSequence,
)


@pytest.fixture
def RE() -> RunEngine:
    return RunEngine()


@pytest.fixture
def region_list() -> list[VGScientaRegion]:
    data_file = os.path.join(TEST_DATA_PATH, "vgscienta_sequence.seq")
    sequence = load_json_file_to_class(VGScientaSequence, data_file)
    return sequence.regions


@pytest.fixture
def excitation_energy_eV() -> float:
    return 1000.0


@pytest.fixture
def analyser_type() -> type[VGScientaAnalyser]:
    return VGScientaAnalyser


@pytest.mark.parametrize("region", ["region_list"], indirect=True)
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


@pytest.mark.parametrize("region", ["region_list"], indirect=True)
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


@pytest.mark.parametrize("region", ["region_list"], indirect=True)
def test_given_region_that_analyser_sets_channel_correctly(
    sim_analyser: VGScientaAnalyser,
    region: VGScientaRegion,
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
