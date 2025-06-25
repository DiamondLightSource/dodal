import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.epics.adcore import ADImageMode
from ophyd_async.testing import (
    assert_configuration,
    assert_value,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.electron_analyser import (
    EnergyMode,
    to_kinetic_energy,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaRegion,
)
from dodal.devices.i09 import LensMode
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_SEQUENCE_REGION_NAMES,
    value,
)


@pytest.fixture
def driver_class() -> type[VGScientaAnalyserDriverIO[LensMode]]:
    return VGScientaAnalyserDriverIO[LensMode]


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_and_reads_correctly(
    sim_driver: VGScientaAnalyserDriverIO,
    region: VGScientaRegion,
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region))

    get_mock_put(sim_driver.image_mode).assert_called_once_with(
        ADImageMode.SINGLE, wait=True
    )
    get_mock_put(sim_driver.detector_mode).assert_called_once_with(
        region.detector_mode, wait=True
    )

    excitation_energy = await sim_driver._get_energy_source(
        region.excitation_energy_source
    ).get_value()

    expected_centre_e = to_kinetic_energy(
        region.fix_energy,
        region.energy_mode,
        excitation_energy,
    )
    get_mock_put(sim_driver.centre_energy).assert_called_once_with(
        expected_centre_e, wait=True
    )
    get_mock_put(sim_driver.energy_step).assert_called_once_with(
        region.energy_step, wait=True
    )

    expected_first_x = region.first_x_channel
    expected_size_x = region.x_channel_size()
    get_mock_put(sim_driver.first_x_channel).assert_called_once_with(
        expected_first_x, wait=True
    )
    get_mock_put(sim_driver.x_channel_size).assert_called_once_with(
        expected_size_x, wait=True
    )

    expected_first_y = region.first_y_channel
    expected_size_y = region.y_channel_size()
    get_mock_put(sim_driver.first_y_channel).assert_called_once_with(
        expected_first_y, wait=True
    )
    get_mock_put(sim_driver.y_channel_size).assert_called_once_with(
        expected_size_y, wait=True
    )

    prefix = sim_driver.name + "-"

    # Check partial match, check only specific fields not covered by abstract class
    await assert_configuration(
        sim_driver,
        {
            f"{prefix}centre_energy": value(expected_centre_e),
            f"{prefix}detector_mode": value(region.detector_mode),
            f"{prefix}energy_step": value(region.energy_step),
            f"{prefix}first_x_channel": value(region.first_x_channel),
            f"{prefix}x_channel_size": value(region.x_channel_size()),
            f"{prefix}first_y_channel": value(region.first_y_channel),
            f"{prefix}y_channel_size": value(region.y_channel_size()),
        },
        full_match=False,
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analayser_binding_energy_is_correct(
    sim_driver: VGScientaAnalyserDriverIO,
    region: VGScientaRegion,
) -> None:
    excitation_energy = await sim_driver._get_energy_source(
        region.excitation_energy_source
    ).get_value()

    # Check binding energy is correct
    energy_axis = [1, 2, 3, 4, 5]
    set_mock_value(sim_driver.energy_axis, np.array(energy_axis, dtype=float))
    is_binding = await sim_driver.energy_mode.get_value() == EnergyMode.BINDING
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_binding else e for e in energy_axis]
    )
    await assert_value(sim_driver.binding_energy_axis, expected_binding_energy_axis)
