from unittest.mock import ANY

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import StrictEnum, init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    assert_value,
    get_mock_put,
    partial_reading,
    set_mock_value,
)

from dodal.devices.electron_analyser import DualEnergySource, EnergyMode
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaRegion,
)
from dodal.devices.i09 import LensMode, PassEnergy, PsuMode
from dodal.testing.electron_analyser import create_driver
from tests.devices.electron_analyser.helper_util import (
    TEST_SEQUENCE_REGION_NAMES,
)


@pytest.fixture
async def sim_driver(
    dual_energy_source: DualEnergySource,
    RE: RunEngine,
) -> VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy]:
    async with init_devices(mock=True):
        sim_driver = await create_driver(
            VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
            prefix="TEST:",
            energy_source=dual_energy_source,
        )
    return sim_driver


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_correctly(
    sim_driver: VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
    region: VGScientaRegion[LensMode, PassEnergy],
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region), wait=True)

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
    excitation_energy = await sim_driver.energy_source.energy.get_value()
    ke_region = region.switch_energy_mode(EnergyMode.KINETIC, excitation_energy)
    get_mock_put(sim_driver.low_energy).assert_called_once_with(
        ke_region.low_energy, wait=True
    )
    get_mock_put(sim_driver.centre_energy).assert_called_once_with(
        ke_region.centre_energy, wait=True
    )
    get_mock_put(sim_driver.high_energy).assert_called_once_with(
        ke_region.high_energy, wait=True
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
    get_mock_put(sim_driver.detector_mode).assert_called_once_with(
        region.detector_mode, wait=True
    )
    get_mock_put(sim_driver.energy_step).assert_called_once_with(
        region.energy_step, wait=True
    )
    get_mock_put(sim_driver.region_min_x).assert_called_once_with(
        region.min_x, wait=True
    )
    get_mock_put(sim_driver.region_size_x).assert_called_once_with(
        region.size_x, wait=True
    )
    get_mock_put(sim_driver.region_min_y).assert_called_once_with(
        region.min_y, wait=True
    )
    get_mock_put(sim_driver.region_size_y).assert_called_once_with(
        region.size_y, wait=True
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_and_read_configuration_is_correct(
    sim_driver: VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
    region: VGScientaRegion[LensMode, PassEnergy],
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region), wait=True)

    prefix = sim_driver.name + "-"
    excitation_energy = await sim_driver.energy_source.energy.get_value()
    ke_region = region.switch_energy_mode(EnergyMode.KINETIC, excitation_energy)
    await assert_configuration(
        sim_driver,
        {
            f"{prefix}region_name": partial_reading(region.name),
            f"{prefix}energy_mode": partial_reading(region.energy_mode),
            f"{prefix}acquisition_mode": partial_reading(region.acquisition_mode),
            f"{prefix}lens_mode": partial_reading(region.lens_mode),
            f"{prefix}low_energy": partial_reading(ke_region.low_energy),
            f"{prefix}centre_energy": partial_reading(ke_region.centre_energy),
            f"{prefix}high_energy": partial_reading(ke_region.high_energy),
            f"{prefix}energy_step": partial_reading(region.energy_step),
            f"{prefix}pass_energy": partial_reading(region.pass_energy),
            f"{prefix}slices": partial_reading(region.slices),
            f"{prefix}iterations": partial_reading(region.iterations),
            f"{prefix}total_steps": partial_reading(ANY),
            f"{prefix}acquire_time": partial_reading(region.acquire_time),
            f"{prefix}total_time": partial_reading(ANY),
            f"{prefix}energy_axis": partial_reading(ANY),
            f"{prefix}binding_energy_axis": partial_reading(ANY),
            f"{prefix}angle_axis": partial_reading(ANY),
            f"{prefix}detector_mode": partial_reading(region.detector_mode),
            f"{prefix}region_min_x": partial_reading(region.min_x),
            f"{prefix}region_size_x": partial_reading(region.size_x),
            f"{prefix}sensor_max_size_x": partial_reading(ANY),
            f"{prefix}region_min_y": partial_reading(region.min_y),
            f"{prefix}region_size_y": partial_reading(region.size_y),
            f"{prefix}sensor_max_size_y": partial_reading(ANY),
            f"{prefix}psu_mode": partial_reading(ANY),
        }
        | await sim_driver.energy_source.read_configuration(),
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_and_read_is_correct(
    sim_driver: VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
    region: VGScientaRegion[LensMode, PassEnergy],
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region), wait=True)

    spectrum = np.array([1, 2, 3, 4, 5], dtype=float)
    expected_total_intensity = np.sum(spectrum)
    set_mock_value(sim_driver.spectrum, spectrum)

    prefix = sim_driver.name + "-"

    await assert_reading(
        sim_driver,
        {
            f"{prefix}energy_source-selected_source": partial_reading(
                region.excitation_energy_source
            ),
            f"{prefix}image": partial_reading(ANY),
            f"{prefix}spectrum": partial_reading(spectrum),
            f"{prefix}total_intensity": partial_reading(expected_total_intensity),
        }
        | await sim_driver.energy_source.read(),
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analayser_binding_energy_is_correct(
    sim_driver: VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
    region: VGScientaRegion[LensMode, PassEnergy],
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region), wait=True)
    excitation_energy = await sim_driver.energy_source.energy.get_value()

    # Check binding energy is correct
    energy_axis = [1, 2, 3, 4, 5]
    set_mock_value(sim_driver.energy_axis, np.array(energy_axis, dtype=float))

    # Check binding energy is correct
    is_region_binding = region.is_binding_energy()
    is_driver_binding = await sim_driver.energy_mode.get_value() == EnergyMode.BINDING
    # Catch that driver correctly reflects what region energy mode is.
    assert is_region_binding == is_driver_binding
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_driver_binding else e for e in energy_axis]
    )
    await assert_value(sim_driver.binding_energy_axis, expected_binding_energy_axis)


def test_driver_throws_error_with_wrong_pass_energy(
    sim_driver: VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
    RE: RunEngine,
) -> None:
    class PassEnergyTestEnum(StrictEnum):
        TEST_1 = "INVALID_PASS_ENERGY"

    pass_energy_datatype = sim_driver.pass_energy.datatype
    pass_energy_datatype_name = (
        pass_energy_datatype.__name__ if pass_energy_datatype is not None else ""
    )
    with pytest.raises(
        FailedStatus, match=f"is not a valid {pass_energy_datatype_name}"
    ):
        RE(bps.mv(sim_driver.pass_energy, PassEnergyTestEnum.TEST_1))


def test_driver_throws_error_with_wrong_detector_mode(
    sim_driver: VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
    RE: RunEngine,
) -> None:
    class DetectorModeTestEnum(StrictEnum):
        TEST_1 = "INVALID_DETECTOR_MODE"

    detector_mode_datatype = sim_driver.detector_mode.datatype
    pass_energy_datatype_name = (
        detector_mode_datatype.__name__ if detector_mode_datatype is not None else ""
    )
    with pytest.raises(
        FailedStatus, match=f"is not a valid {pass_energy_datatype_name}"
    ):
        RE(bps.mv(sim_driver.detector_mode, DetectorModeTestEnum.TEST_1))
