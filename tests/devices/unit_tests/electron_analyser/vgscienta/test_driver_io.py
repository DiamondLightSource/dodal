import numpy as np
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.epics.adcore import ADImageMode
from ophyd_async.testing import (
    get_mock_put,
    set_mock_value,
)

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser import (
    EnergyMode,
    to_kinetic_energy,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaRegion,
    VGScientaSequence,
)
from dodal.plan_stubs.electron_analyser import configure_vgscienta
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SEQUENCE_REGION_NAMES,
    TEST_VGSCIENTA_SEQUENCE,
    assert_read_configuration_has_expected_value,
)


@pytest.fixture
def driver_class() -> type[VGScientaAnalyserDriverIO]:
    return VGScientaAnalyserDriverIO


@pytest.fixture
def sequence() -> VGScientaSequence:
    return load_json_file_to_class(VGScientaSequence, TEST_VGSCIENTA_SEQUENCE)


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_modes_correctly(
    sim_driver: VGScientaAnalyserDriverIO,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_vgscienta(sim_driver, region, excitation_energy))

    get_mock_put(sim_driver.detector_mode).assert_called_once_with(
        region.detector_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "detector_mode", region.detector_mode
    )
    get_mock_put(sim_driver.image_mode).assert_called_once_with(
        ADImageMode.SINGLE, wait=True
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_driver: VGScientaAnalyserDriverIO,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_vgscienta(sim_driver, region, excitation_energy))

    expected_centre_e = to_kinetic_energy(
        region.fix_energy, region.energy_mode, excitation_energy
    )
    get_mock_put(sim_driver.centre_energy).assert_called_once_with(
        expected_centre_e, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "centre_energy", expected_centre_e
    )
    get_mock_put(sim_driver.energy_step).assert_called_once_with(
        region.energy_step, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "energy_step", region.energy_step
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_vgscienta_sets_channel_correctly(
    sim_driver: VGScientaAnalyserDriverIO,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_vgscienta(sim_driver, region, excitation_energy))

    expected_first_x = region.first_x_channel
    expected_size_x = region.x_channel_size()
    get_mock_put(sim_driver.first_x_channel).assert_called_once_with(
        expected_first_x, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "first_x_channel", expected_first_x
    )
    get_mock_put(sim_driver.x_channel_size).assert_called_once_with(
        expected_size_x, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "x_channel_size", expected_size_x
    )

    expected_first_y = region.first_y_channel
    expected_size_y = region.y_channel_size()
    get_mock_put(sim_driver.first_y_channel).assert_called_once_with(
        expected_first_y, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "first_y_channel", expected_first_y
    )
    get_mock_put(sim_driver.y_channel_size).assert_called_once_with(
        expected_size_y, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "y_channel_size", expected_size_y
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_that_data_to_read_is_correct(
    sim_driver: VGScientaAnalyserDriverIO,
    region: VGScientaRegion,
    excitation_energy: float,
    RE: RunEngine,
):
    RE(configure_vgscienta(sim_driver, region, excitation_energy))

    # Check binding energy is correct
    energy_axis = [1, 2, 3, 4, 5]
    set_mock_value(sim_driver.energy_axis, np.array(energy_axis, dtype=float))
    is_binding = await sim_driver.energy_mode.get_value() == EnergyMode.BINDING
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_binding else e for e in energy_axis]
    )
    assert np.array_equal(
        await sim_driver.binding_energy_axis.get_value(),
        expected_binding_energy_axis,
    )
