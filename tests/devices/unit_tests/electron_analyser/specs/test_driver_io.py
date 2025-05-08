import numpy as np
import pytest
from bluesky.plan_stubs import mv
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    get_mock_put,
    set_mock_value,
)

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsRegion,
    SpecsSequence,
)
from dodal.devices.electron_analyser.types import EnergyMode
from dodal.plan_stubs.electron_analyser import configure_specs
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SEQUENCE_REGION_NAMES,
    TEST_SPECS_SEQUENCE,
    assert_read_configuration_has_expected_value,
)


@pytest.fixture
def driver_class() -> type[SpecsAnalyserDriverIO]:
    return SpecsAnalyserDriverIO


@pytest.fixture
def sequence() -> SpecsSequence:
    return load_json_file_to_class(SpecsSequence, TEST_SPECS_SEQUENCE)


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=["region"])
async def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_driver: SpecsAnalyserDriverIO,
    region: SpecsRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_specs(sim_driver, region, excitation_energy))

    if region.acquisition_mode == "Fixed Energy":
        get_mock_put(sim_driver.energy_step).assert_called_once_with(
            region.energy_step, wait=True
        )
        await assert_read_configuration_has_expected_value(
            sim_driver, "energy_step", region.energy_step
        )
    else:
        get_mock_put(sim_driver.energy_step).assert_not_called()

    if region.acquisition_mode == "Fixed Transmission":
        get_mock_put(sim_driver.centre_energy).assert_called_once_with(
            region.centre_energy, wait=True
        )
        await assert_read_configuration_has_expected_value(
            sim_driver, "centre_energy", region.centre_energy
        )
    else:
        get_mock_put(sim_driver.centre_energy).assert_not_called()


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=["region"])
async def test_given_region_that_analyser_sets_modes_correctly(
    sim_driver: SpecsAnalyserDriverIO,
    region: SpecsRegion,
    excitation_energy: float,
    RE: RunEngine,
) -> None:
    RE(configure_specs(sim_driver, region, excitation_energy))

    get_mock_put(sim_driver.psu_mode).assert_called_once_with(
        region.psu_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "psu_mode", region.psu_mode
    )

    get_mock_put(sim_driver.snapshot_values).assert_called_once_with(
        region.values, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "snapshot_values", region.values
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_that_data_to_read_is_correct(
    sim_driver: SpecsAnalyserDriverIO,
    region: SpecsRegion,
    excitation_energy: float,
    RE: RunEngine,
):
    RE(configure_specs(sim_driver, region, excitation_energy))

    # Check binding energy is correct
    is_binding = await sim_driver.energy_mode.get_value() == EnergyMode.BINDING
    energy_axis = await sim_driver.energy_axis.get_value()
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_binding else e for e in energy_axis]
    )
    assert np.array_equal(
        await sim_driver.binding_energy_axis.get_value(),
        expected_binding_energy_axis,
    )


async def test_specs_analyser_energy_axis(
    sim_driver: SpecsAnalyserDriverIO,
    RE: RunEngine,
) -> None:
    start_energy = 1
    end_energy = 10
    total_points_iterations = 11

    RE(mv(sim_driver.low_energy, start_energy))
    RE(mv(sim_driver.high_energy, end_energy))
    RE(mv(sim_driver.slices, total_points_iterations))

    energy_axis = await sim_driver.energy_axis.get_value()
    expected_energy_axis = [1.0, 1.9, 2.8, 3.7, 4.6, 5.5, 6.4, 7.3, 8.2, 9.1, 10.0]
    np.testing.assert_array_equal(energy_axis, expected_energy_axis)


async def test_specs_analyser_angle_axis(
    sim_driver: SpecsAnalyserDriverIO,
    RE: RunEngine,
) -> None:
    max_angle = 21
    min_angle = 1
    slices = 10

    set_mock_value(sim_driver.min_angle_axis, min_angle)
    set_mock_value(sim_driver.max_angle_axis, max_angle)
    RE(mv(sim_driver.slices, slices))

    angle_axis = await sim_driver.angle_axis.get_value()
    expected_angle_axis = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    np.testing.assert_array_equal(angle_axis, expected_angle_axis)
