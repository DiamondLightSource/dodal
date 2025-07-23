from typing import Any

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import SignalR
from ophyd_async.testing import (
    assert_configuration,
    assert_value,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.b07 import LensMode, PsuMode
from dodal.devices.electron_analyser import EnergyMode
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsRegion,
)
from tests.devices.unit_tests.electron_analyser.helpers import (
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
async def test_analyser_sets_region_and_configuration_is_correct(
    sim_driver: SpecsAnalyserDriverIO[LensMode, PsuMode],
    region: SpecsRegion[LensMode, PsuMode],
    expected_abstract_driver_config_reading: dict[str, dict[str, Any]],
    RE: RunEngine,
) -> None:
    get_mock_put(sim_driver.psu_mode).assert_called_once_with(
        region.psu_mode, wait=True
    )

    get_mock_put(sim_driver.snapshot_values).assert_called_once_with(
        region.values, wait=True
    )

    prefix = sim_driver.name + "-"
    specs_expected_config_reading = {
        f"{prefix}snapshot_values": {"value": region.values},
        f"{prefix}psu_mode": {"value": region.psu_mode},
    }

    full_expected_config = (
        expected_abstract_driver_config_reading | specs_expected_config_reading
    )

    # Check match by combining expected specs specific config reading with abstract one
    await assert_configuration(sim_driver, full_expected_config)


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
