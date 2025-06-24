import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import StrictEnum
from ophyd_async.epics.adcore import ADImageMode
from ophyd_async.testing import assert_configuration, get_mock_put, set_mock_value

from dodal.devices.electron_analyser import (
    EnergyMode,
    to_kinetic_energy,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaRegion,
)
from dodal.devices.i09 import LensMode, PassEnergy, PsuMode
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_SEQUENCE_REGION_NAMES,
)


@pytest.fixture
def driver_class() -> type[VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy]]:
    return VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy]


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

    # Check partial match, check only specific fields not covered by abstract class
    await assert_configuration(
        sim_driver,
        {
            "sim_driver-centre_energy": {"value": expected_centre_e},
            "sim_driver-detector_mode": {"value": region.detector_mode},
            "sim_driver-energy_step": {"value": region.energy_step},
            "sim_driver-first_x_channel": {"value": region.first_x_channel},
            "sim_driver-x_channel_size": {"value": region.x_channel_size()},
            "sim_driver-first_y_channel": {"value": region.first_y_channel},
            "sim_driver-y_channel_size": {"value": region.y_channel_size()},
        },
        # full_match=False,
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
    assert np.array_equal(
        await sim_driver.binding_energy_axis.get_value(),
        expected_binding_energy_axis,
    )


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
