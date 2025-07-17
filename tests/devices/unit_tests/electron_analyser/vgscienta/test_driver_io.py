from typing import Any

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import SignalR, StrictEnum
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
    VGScientaSequence,
)
from dodal.devices.i09 import LensMode, PassEnergy, PsuMode
from tests.devices.unit_tests.electron_analyser.helpers import (
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
async def test_analyser_sets_region_and_reads_correctly(
    sim_driver: VGScientaAnalyserDriverIO,
    sequence: VGScientaSequence,
    region: VGScientaRegion,
    expected_abstract_driver_config_reading: dict[str, dict[str, Any]],
    RE: RunEngine,
) -> None:
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
        region.centre_energy,
        region.energy_mode,
        excitation_energy,
    )
    get_mock_put(sim_driver.centre_energy).assert_called_once_with(
        expected_centre_e, wait=True
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

    set_mock_value(sim_driver.psu_mode, sequence.psu_mode)

    prefix = sim_driver.name + "-"
    vgscienta_expected_config_reading = {
        f"{prefix}centre_energy": {"value": expected_centre_e},
        f"{prefix}detector_mode": {"value": region.detector_mode},
        f"{prefix}energy_step": {"value": region.energy_step},
        f"{prefix}region_min_x": {"value": region.min_x},
        f"{prefix}region_size_x": {"value": region.size_x},
        f"{prefix}sensor_max_size_x": {"value": 0},  # ToDo
        f"{prefix}region_min_y": {"value": region.min_y},
        f"{prefix}region_size_y": {"value": region.size_y},
        f"{prefix}sensor_max_size_y": {"value": 0},  # ToDo
        f"{prefix}psu_mode": {"value": sequence.psu_mode},
    }

    full_expected_config = (
        expected_abstract_driver_config_reading | vgscienta_expected_config_reading
    )

    # Check match by combining expected vgscienta specific config reading with abstract
    # one
    await assert_configuration(sim_driver, full_expected_config)


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
