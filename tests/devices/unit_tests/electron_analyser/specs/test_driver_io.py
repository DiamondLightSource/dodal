import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    assert_configuration,
    assert_value,
    get_mock_put,
    partial_reading,
    set_mock_value,
)

from dodal.devices.b07 import LensMode, PsuMode
from dodal.devices.electron_analyser import EnergyMode, to_kinetic_energy
from dodal.devices.electron_analyser.specs import (
    AcquisitionMode,
    SpecsAnalyserDriverIO,
    SpecsRegion,
)
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_SEQUENCE_REGION_NAMES,
)


@pytest.fixture
def driver_class() -> type[SpecsAnalyserDriverIO[LensMode, PsuMode]]:
    return SpecsAnalyserDriverIO[LensMode, PsuMode]


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_and_configuration_is_correct(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    region: SpecsRegion[LensMode, PsuMode],
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region))
    # ToDo - Put energy step and centre energy into abstract, remove if statements.
    if region.acquisition_mode == AcquisitionMode.FIXED_TRANSMISSION:
        get_mock_put(sim_driver.energy_step).assert_called_once_with(
            region.energy_step, wait=True
        )
    else:
        get_mock_put(sim_driver.energy_step).assert_not_called()

    if region.acquisition_mode == AcquisitionMode.FIXED_ENERGY:
        source = sim_driver._get_energy_source(region.excitation_energy_source)
        excitation_energy = await source.get_value()
        expected_centre_e = to_kinetic_energy(
            region.centre_energy, region.energy_mode, excitation_energy
        )
        get_mock_put(sim_driver.centre_energy).assert_called_once_with(
            expected_centre_e, wait=True
        )
    else:
        get_mock_put(sim_driver.centre_energy).assert_not_called()

    get_mock_put(sim_driver.psu_mode).assert_called_once_with(
        region.psu_mode, wait=True
    )

    get_mock_put(sim_driver.snapshot_values).assert_called_once_with(
        region.values, wait=True
    )

    prefix = sim_driver.name + "-"
    # Check partial match, check only specific fields not covered by abstract class
    await assert_configuration(
        sim_driver,
        {
            f"{prefix}centre_energy": partial_reading(
                await sim_driver.centre_energy.get_value()
            ),
            f"{prefix}energy_step": partial_reading(
                await sim_driver.energy_step.get_value()
            ),
            f"{prefix}psu_mode": partial_reading(region.psu_mode),
            f"{prefix}snapshot_values": partial_reading(region.values),
        },
        full_match=False,
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_specs_analyser_binding_energy_axis(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    region: SpecsRegion[LensMode, PsuMode],
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region))

    source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await source.get_value()

    # Check binding energy is correct
    is_binding = await sim_driver.energy_mode.get_value() == EnergyMode.BINDING
    energy_axis = await sim_driver.energy_axis.get_value()
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_binding else e for e in energy_axis]
    )
    await assert_value(sim_driver.binding_energy_axis, expected_binding_energy_axis)


async def test_specs_analyser_energy_axis(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    RE: RunEngine,
) -> None:
    start_energy = 1
    end_energy = 10
    total_points_iterations = 11

    RE(bps.mv(sim_driver.low_energy, start_energy))
    RE(bps.mv(sim_driver.high_energy, end_energy))
    set_mock_value(sim_driver.energy_channels, total_points_iterations)

    expected_energy_axis = [1.0, 1.9, 2.8, 3.7, 4.6, 5.5, 6.4, 7.3, 8.2, 9.1, 10.0]
    await assert_value(sim_driver.energy_axis, expected_energy_axis)


async def test_specs_analyser_angle_axis(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    RE: RunEngine,
) -> None:
    max_angle = 21
    min_angle = 1
    slices = 10

    set_mock_value(sim_driver.min_angle_axis, min_angle)
    set_mock_value(sim_driver.max_angle_axis, max_angle)
    RE(bps.mv(sim_driver.slices, slices))

    expected_angle_axis = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    await assert_value(sim_driver.angle_axis, expected_angle_axis)
