from unittest.mock import ANY

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import SignalR, StrictEnum
from ophyd_async.epics.adcore import ADImageMode
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    assert_value,
    get_mock_put,
    partial_reading,
    set_mock_value,
)

from dodal.devices.electron_analyser import EnergyMode
from dodal.devices.electron_analyser.util import to_kinetic_energy
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaRegion,
)
from dodal.devices.i09 import LensMode, PassEnergy, PsuMode
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_SEQUENCE_REGION_NAMES,
    create_analyser_device,
)


@pytest.fixture
async def sim_driver(
    energy_sources: dict[str, SignalR[float]],
) -> VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy]:
    return await create_analyser_device(
        VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
        energy_sources,
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_correctly(
    sim_driver: VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
    region: VGScientaRegion[LensMode, PassEnergy],
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region), wait=True)

    energy_source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await energy_source.get_value()

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

    expected_low_e = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    get_mock_put(sim_driver.low_energy).assert_called_once_with(
        expected_low_e, wait=True
    )
    expected_centre_e = to_kinetic_energy(
        region.centre_energy, region.energy_mode, excitation_energy
    )
    get_mock_put(sim_driver.centre_energy).assert_called_once_with(
        expected_centre_e, wait=True
    )
    expected_high_e = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )
    get_mock_put(sim_driver.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )
    get_mock_put(sim_driver.pass_energy).assert_called_once_with(
        region.pass_energy, wait=True
    )
    expected_source = energy_source.name
    get_mock_put(sim_driver.excitation_energy_source).assert_called_once_with(
        expected_source, wait=True
    )
    get_mock_put(sim_driver.slices).assert_called_once_with(region.slices, wait=True)
    get_mock_put(sim_driver.iterations).assert_called_once_with(
        region.iterations, wait=True
    )

    get_mock_put(sim_driver.image_mode).assert_called_once_with(
        ADImageMode.SINGLE, wait=True
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

    energy_source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await energy_source.get_value()
    expected_source = energy_source.name

    expected_low_e = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    expected_centre_e = to_kinetic_energy(
        region.centre_energy, region.energy_mode, excitation_energy
    )
    expected_high_e = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )

    await assert_configuration(
        sim_driver,
        {
            f"{prefix}region_name": partial_reading(region.name),
            f"{prefix}energy_mode": partial_reading(region.energy_mode),
            f"{prefix}acquisition_mode": partial_reading(region.acquisition_mode),
            f"{prefix}lens_mode": partial_reading(region.lens_mode),
            f"{prefix}low_energy": partial_reading(expected_low_e),
            f"{prefix}centre_energy": partial_reading(expected_centre_e),
            f"{prefix}high_energy": partial_reading(expected_high_e),
            f"{prefix}energy_step": partial_reading(region.energy_step),
            f"{prefix}pass_energy": partial_reading(region.pass_energy),
            f"{prefix}excitation_energy_source": partial_reading(expected_source),
            f"{prefix}slices": partial_reading(region.slices),
            f"{prefix}iterations": partial_reading(region.iterations),
            f"{prefix}total_steps": partial_reading(ANY),
            f"{prefix}step_time": partial_reading(ANY),
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
        },
    )


@pytest.fixture
async def test_analyser_sets_region_and_read_is_correct(
    sim_driver: VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
    region: VGScientaRegion[LensMode, PassEnergy],
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
            f"{prefix}excitation_energy": partial_reading(excitation_energy),
            f"{prefix}image": partial_reading(ANY),
            f"{prefix}spectrum": partial_reading(spectrum),
            f"{prefix}total_intensity": partial_reading(expected_total_intensity),
        },
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analayser_binding_energy_is_correct(
    sim_driver: VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy],
    region: VGScientaRegion[LensMode, PassEnergy],
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
