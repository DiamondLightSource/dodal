from unittest.mock import ANY

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import SignalR
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    assert_value,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.b07 import LensMode, PsuMode
from dodal.devices.electron_analyser import (
    EnergyMode,
    to_kinetic_energy,
)
from dodal.devices.electron_analyser.specs import (
    AcquisitionMode,
    SpecsAnalyserDriverIO,
    SpecsRegion,
)
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_SEQUENCE_REGION_NAMES,
    create_analyser_device,
)


@pytest.fixture
async def sim_driver(
    energy_sources: dict[str, SignalR[float]],
) -> SpecsAnalyserDriverIO[LensMode, PsuMode]:
    return await create_analyser_device(
        SpecsAnalyserDriverIO[LensMode, PsuMode],
        energy_sources,
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_correctly(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    region: SpecsRegion[LensMode, PsuMode],
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region), wait=True)

    energy_source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await energy_source.get_value()
    expected_source = energy_source.name

    expected_low_e = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    expected_high_e = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )

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
        expected_low_e, wait=True
    )
    if region.acquisition_mode == AcquisitionMode.FIXED_ENERGY:
        expected_centre_e = to_kinetic_energy(
            region.centre_energy, region.energy_mode, excitation_energy
        )
        get_mock_put(sim_driver.centre_energy).assert_called_once_with(
            expected_centre_e, wait=True
        )
    else:
        get_mock_put(sim_driver.centre_energy).assert_not_called()

    get_mock_put(sim_driver.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )
    get_mock_put(sim_driver.pass_energy).assert_called_once_with(
        region.pass_energy, wait=True
    )
    get_mock_put(sim_driver.excitation_energy_source).assert_called_once_with(
        expected_source, wait=True
    )
    get_mock_put(sim_driver.slices).assert_called_once_with(region.slices, wait=True)
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
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region), wait=True)

    prefix = sim_driver.name + "-"

    energy_source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await energy_source.get_value()
    expected_source = energy_source.name

    expected_low_e = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    expected_high_e = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )

    await assert_configuration(
        sim_driver,
        {
            f"{prefix}region_name": {"value": region.name},
            f"{prefix}energy_mode": {"value": region.energy_mode},
            f"{prefix}acquisition_mode": {"value": region.acquisition_mode},
            f"{prefix}lens_mode": {"value": region.lens_mode},
            f"{prefix}low_energy": {"value": expected_low_e},
            f"{prefix}centre_energy": {"value": ANY},
            f"{prefix}high_energy": {"value": expected_high_e},
            f"{prefix}energy_step": {"value": ANY},
            f"{prefix}pass_energy": {"value": region.pass_energy},
            f"{prefix}excitation_energy_source": {"value": expected_source},
            f"{prefix}slices": {"value": region.slices},
            f"{prefix}iterations": {"value": region.iterations},
            f"{prefix}total_steps": {"value": ANY},
            f"{prefix}step_time": {"value": ANY},
            f"{prefix}total_time": {"value": ANY},
            f"{prefix}energy_axis": {"value": ANY},
            f"{prefix}binding_energy_axis": {"value": ANY},
            f"{prefix}angle_axis": {"value": ANY},
            f"{prefix}snapshot_values": {"value": region.values},
            f"{prefix}psu_mode": {"value": region.psu_mode},
        },
    )


@pytest.fixture
async def test_analyser_sets_region_and_read_is_correct(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    region: SpecsRegion[LensMode, PsuMode],
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region), wait=True)

    energy_source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await energy_source.get_value()

    spectrum = np.array([1, 2, 3, 4, 5], dtype=float)
    expected_total_intensity = np.sum(spectrum)
    set_mock_value(sim_driver.spectrum, spectrum)

    prefix = sim_driver.name + "-"
    await assert_reading(
        sim_driver,
        {
            f"{prefix}excitation_energy": {"value": excitation_energy},
            f"{prefix}image": {"value": []},
            f"{prefix}spectrum": {"value": spectrum},
            f"{prefix}total_intensity": {"value": expected_total_intensity},
        },
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
