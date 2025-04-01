import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    get_mock_put,
)

from dodal.devices.electron_analyser.util import to_kinetic_energy
from dodal.devices.electron_analyser.vgscienta_analyser_controller import (
    VGScientaAnalyserController,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    VGScientaRegion,
    VGScientaSequence,
)
from dodal.plan_stubs.electron_analyser.configure_controller import configure_vgscienta
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SEQUENCE_REGION_NAMES,
    TEST_VGSCIENTA_SEQUENCE,
)


@pytest.fixture
def sequence_file() -> str:
    return TEST_VGSCIENTA_SEQUENCE


@pytest.fixture
def sequence_class() -> type[VGScientaSequence]:
    return VGScientaSequence


@pytest.fixture
def analyser_type() -> type[VGScientaAnalyserController]:
    return VGScientaAnalyserController


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_modes_correctly(
    sim_analyser: VGScientaAnalyserController,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_vgscienta(sim_analyser, region, excitation_energy))

    get_mock_put(sim_analyser.detector_mode).assert_called_once_with(
        region.detector_mode, wait=True
    )
    get_mock_put(sim_analyser.image_mode).assert_called_once_with("Single", wait=True)


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_analyser: VGScientaAnalyserController,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_vgscienta(sim_analyser, region, excitation_energy))

    expected_centre_e = to_kinetic_energy(
        region.fix_energy, region.energy_mode, excitation_energy
    )
    get_mock_put(sim_analyser.centre_energy).assert_called_once_with(
        expected_centre_e, wait=True
    )
    get_mock_put(sim_analyser.energy_step).assert_called_once_with(
        region.energy_step, wait=True
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
def test_given_region_that_analyser_sets_channel_correctly(
    sim_analyser: VGScientaAnalyserController,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_vgscienta(sim_analyser, region, excitation_energy))

    expected_first_x = region.first_x_channel
    expected_size_x = region.x_channel_size()
    get_mock_put(sim_analyser.first_x_channel).assert_called_once_with(
        expected_first_x, wait=True
    )
    get_mock_put(sim_analyser.x_channel_size).assert_called_once_with(
        expected_size_x, wait=True
    )

    expected_first_y = region.first_y_channel
    expected_size_y = region.y_channel_size()
    get_mock_put(sim_analyser.first_y_channel).assert_called_once_with(
        expected_first_y, wait=True
    )
    get_mock_put(sim_analyser.y_channel_size).assert_called_once_with(
        expected_size_y, wait=True
    )
