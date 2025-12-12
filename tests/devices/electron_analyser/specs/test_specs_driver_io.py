from unittest.mock import ANY

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    assert_value,
    partial_reading,
)

from dodal.devices.b07 import LensMode, PsuMode
from dodal.devices.electron_analyser.base import EnergyMode
from dodal.devices.electron_analyser.base.base_enums import EnergyMode
from dodal.devices.electron_analyser.specs import (
    AcquisitionMode,
    SpecsAnalyserDriverIO,
    SpecsRegion,
)
from dodal.testing.electron_analyser import create_driver
from tests.devices.electron_analyser.helper_util import (
    TEST_SEQUENCE_REGION_NAMES,
)


@pytest.fixture
async def sim_driver() -> SpecsAnalyserDriverIO[LensMode, PsuMode]:
    async with init_devices(mock=True):
        sim_driver = create_driver(
            SpecsAnalyserDriverIO[LensMode, PsuMode],
            prefix="TEST:",
        )
    return sim_driver


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_correctly(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    region: SpecsRegion[LensMode, PsuMode],
    run_engine: RunEngine,
) -> None:
    run_engine(bps.mv(sim_driver, region), wait=True)

    get_mock_put(sim_driver.region_name).assert_called_once_with(region.name, wait=True)
    get_mock_put(sim_driver.energy_mode).assert_called_once_with(
        region.energy_mode, wait=True
    )
    get_mock_put(sim_driver.acquisition_mode).assert_called_once_with(
        region.acquisition_mode, wait=True
    )
    get_mock_put(sim_driver.lens_mode).assert_called_once_with(
        region.lens_mode, wait=True
    )
    get_mock_put(sim_driver.low_energy).assert_called_once_with(
        region.low_energy, wait=True
    )
    if region.acquisition_mode == AcquisitionMode.FIXED_ENERGY:
        get_mock_put(sim_driver.centre_energy).assert_called_once_with(
            region.centre_energy, wait=True
        )
    else:
        get_mock_put(sim_driver.centre_energy).assert_not_called()

    get_mock_put(sim_driver.high_energy).assert_called_once_with(
        region.high_energy, wait=True
    )
    get_mock_put(sim_driver.pass_energy).assert_called_once_with(
        region.pass_energy, wait=True
    )
    get_mock_put(sim_driver.slices).assert_called_once_with(region.slices, wait=True)
    get_mock_put(sim_driver.acquire_time).assert_called_once_with(
        region.acquire_time, wait=True
    )
    get_mock_put(sim_driver.iterations).assert_called_once_with(
        region.iterations, wait=True
    )

    if region.acquisition_mode == AcquisitionMode.FIXED_TRANSMISSION:
        get_mock_put(sim_driver.energy_step).assert_called_once_with(
            region.energy_step, wait=True
        )
    else:
        get_mock_put(sim_driver.energy_step).assert_not_called()

    get_mock_put(sim_driver.psu_mode).assert_called_once_with(
        region.psu_mode, wait=True
    )
    get_mock_put(sim_driver.snapshot_values).assert_called_once_with(
        region.values, wait=True
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_and_read_configuration_is_correct(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    region: SpecsRegion[LensMode, PsuMode],
    run_engine: RunEngine,
) -> None:
    run_engine(bps.mv(sim_driver, region), wait=True)

    prefix = sim_driver.name + "-"

    await assert_configuration(
        sim_driver,
        {
            f"{prefix}region_name": partial_reading(region.name),
            f"{prefix}energy_mode": partial_reading(region.energy_mode),
            f"{prefix}acquisition_mode": partial_reading(region.acquisition_mode),
            f"{prefix}lens_mode": partial_reading(region.lens_mode),
            f"{prefix}low_energy": partial_reading(region.low_energy),
            f"{prefix}centre_energy": partial_reading(ANY),
            f"{prefix}high_energy": partial_reading(region.high_energy),
            f"{prefix}energy_step": partial_reading(ANY),
            f"{prefix}pass_energy": partial_reading(region.pass_energy),
            f"{prefix}slices": partial_reading(region.slices),
            f"{prefix}acquire_time": partial_reading(region.acquire_time),
            f"{prefix}iterations": partial_reading(region.iterations),
            f"{prefix}total_steps": partial_reading(ANY),
            f"{prefix}total_time": partial_reading(ANY),
            f"{prefix}energy_axis": partial_reading(ANY),
            f"{prefix}binding_energy_axis": partial_reading(ANY),
            f"{prefix}angle_axis": partial_reading(ANY),
            f"{prefix}snapshot_values": partial_reading(region.values),
            f"{prefix}psu_mode": partial_reading(region.psu_mode),
            f"{prefix}cached_excitation_energy": partial_reading(0),
        },
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_and_read_is_correct(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    region: SpecsRegion[LensMode, PsuMode],
    run_engine: RunEngine,
) -> None:
    run_engine(bps.mv(sim_driver, region), wait=True)

    spectrum = np.array([1, 2, 3, 4, 5], dtype=float)
    expected_total_intensity = np.sum(spectrum)
    set_mock_value(sim_driver.spectrum, spectrum)

    prefix = sim_driver.name + "-"
    await assert_reading(
        sim_driver,
        {
            f"{prefix}image": partial_reading([]),
            f"{prefix}spectrum": partial_reading(spectrum),
            f"{prefix}total_intensity": partial_reading(expected_total_intensity),
        },
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_specs_analyser_binding_energy_axis(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    region: SpecsRegion[LensMode, PsuMode],
    run_engine: RunEngine,
) -> None:
    run_engine(bps.mv(sim_driver, region))

    excitation_energy = 500
    await sim_driver.cached_excitation_energy.set(500)

    # Check binding energy is correct
    is_region_binding = region.is_binding_energy()
    is_driver_binding = await sim_driver.energy_mode.get_value() == EnergyMode.BINDING
    # Catch that driver correctly reflects what region energy mode is.
    assert is_region_binding == is_driver_binding
    energy_axis = await sim_driver.energy_axis.get_value()
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_driver_binding else e for e in energy_axis]
    )
    await assert_value(sim_driver.binding_energy_axis, expected_binding_energy_axis)


async def test_specs_analyser_energy_axis(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    run_engine: RunEngine,
) -> None:
    start_energy = 1
    end_energy = 10
    total_points_iterations = 11

    run_engine(bps.mv(sim_driver.low_energy, start_energy))
    run_engine(bps.mv(sim_driver.high_energy, end_energy))
    set_mock_value(sim_driver.energy_channels, total_points_iterations)

    expected_energy_axis = [1.0, 1.9, 2.8, 3.7, 4.6, 5.5, 6.4, 7.3, 8.2, 9.1, 10.0]
    await assert_value(sim_driver.energy_axis, expected_energy_axis)


async def test_specs_analyser_angle_axis(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    run_engine: RunEngine,
) -> None:
    max_angle = 21
    min_angle = 1
    slices = 10

    set_mock_value(sim_driver.min_angle_axis, min_angle)
    set_mock_value(sim_driver.max_angle_axis, max_angle)
    run_engine(bps.mv(sim_driver.slices, slices))

    expected_angle_axis = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    await assert_value(sim_driver.angle_axis, expected_angle_axis)
