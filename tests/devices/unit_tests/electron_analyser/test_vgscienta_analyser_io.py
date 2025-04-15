import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.epics.adcore import ADImageMode
from ophyd_async.testing import (
    get_mock_put,
)

from dodal.devices.electron_analyser.util import to_kinetic_energy
from dodal.devices.electron_analyser.vgscienta_analyser_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    VGScientaRegion,
    VGScientaSequence,
)
from dodal.plan_stubs.electron_analyser.configure_controller import configure_vgscienta
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SEQUENCE_REGION_NAMES,
    TEST_VGSCIENTA_SEQUENCE,
    assert_reading_has_expected_value,
)


@pytest.fixture
def sequence_file() -> str:
    return TEST_VGSCIENTA_SEQUENCE


@pytest.fixture
def sequence_class() -> type[VGScientaSequence]:
    return VGScientaSequence


@pytest.fixture
def analyser_type() -> type[VGScientaAnalyserDriverIO]:
    return VGScientaAnalyserDriverIO


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_modes_correctly(
    sim_analyser_driver: VGScientaAnalyserDriverIO,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_vgscienta(sim_analyser_driver, region, excitation_energy))

    get_mock_put(sim_analyser_driver.detector_mode).assert_called_once_with(
        region.detector_mode, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "detector_mode", region.detector_mode
    )
    get_mock_put(sim_analyser_driver.adbase_cam.image_mode).assert_called_once_with(
        ADImageMode.SINGLE, wait=True
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_analyser_driver: VGScientaAnalyserDriverIO,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_vgscienta(sim_analyser_driver, region, excitation_energy))

    expected_centre_e = to_kinetic_energy(
        region.fix_energy, region.energy_mode, excitation_energy
    )
    get_mock_put(sim_analyser_driver.centre_energy).assert_called_once_with(
        expected_centre_e, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "centre_energy", expected_centre_e
    )
    get_mock_put(sim_analyser_driver.energy_step).assert_called_once_with(
        region.energy_step, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "energy_step", region.energy_step
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_vgscienta_sets_channel_correctly(
    sim_analyser_driver: VGScientaAnalyserDriverIO,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_vgscienta(sim_analyser_driver, region, excitation_energy))

    expected_first_x = region.first_x_channel
    expected_size_x = region.x_channel_size()
    get_mock_put(sim_analyser_driver.first_x_channel).assert_called_once_with(
        expected_first_x, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "first_x_channel", expected_first_x
    )
    get_mock_put(sim_analyser_driver.x_channel_size).assert_called_once_with(
        expected_size_x, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "x_channel_size", expected_size_x
    )

    expected_first_y = region.first_y_channel
    expected_size_y = region.y_channel_size()
    get_mock_put(sim_analyser_driver.first_y_channel).assert_called_once_with(
        expected_first_y, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "first_y_channel", expected_first_y
    )
    get_mock_put(sim_analyser_driver.y_channel_size).assert_called_once_with(
        expected_size_y, wait=True
    )
    await assert_reading_has_expected_value(
        sim_analyser_driver, "y_channel_size", expected_size_y
    )
