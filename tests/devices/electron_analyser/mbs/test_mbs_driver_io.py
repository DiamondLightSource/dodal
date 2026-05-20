from unittest.mock import ANY

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import get_mock_put, init_devices
from ophyd_async.testing import assert_configuration, partial_reading

from dodal.devices.beamlines.i05_shared import LensMode, PassEnergy
from dodal.devices.electron_analyser.mbs import (
    AcquisitionMode,
    MbsAnalyserDriverIO,
    MbsRegion,
)
from tests.devices.electron_analyser.helper_util import load_i05_mbs_test_xml_seq


@pytest.fixture
async def sim_driver() -> MbsAnalyserDriverIO[LensMode, PassEnergy]:
    with init_devices(mock=True):
        sim_driver = MbsAnalyserDriverIO("TEST:", LensMode, PassEnergy)
    return sim_driver


@pytest.mark.parametrize("region", load_i05_mbs_test_xml_seq().regions)
async def test_analyser_sets_region_correctly(
    sim_driver: MbsAnalyserDriverIO[LensMode, PassEnergy],
    region: MbsRegion[LensMode, PassEnergy],
    run_engine: RunEngine,
) -> None:
    run_engine(bps.mv(sim_driver, region), wait=True)

    get_mock_put(sim_driver.region_name).assert_called_once_with(region.name)
    get_mock_put(sim_driver.energy_mode).assert_called_once_with(region.energy_mode)
    get_mock_put(sim_driver.acquisition_mode).assert_called_once_with(
        region.acquisition_mode
    )
    get_mock_put(sim_driver.lens_mode).assert_called_once_with(region.lens_mode)
    get_mock_put(sim_driver.low_energy).assert_called_once_with(region.low_energy)
    get_mock_put(sim_driver.centre_energy).assert_called_once_with(region.centre_energy)
    get_mock_put(sim_driver.high_energy).assert_called_once_with(region.high_energy)
    get_mock_put(sim_driver.deflector_x).assert_awaited_once_with(region.deflector_x)
    get_mock_put(sim_driver.pass_energy).assert_called_once_with(region.pass_energy)
    get_mock_put(sim_driver.acquire_time).assert_called_once_with(region.acquire_time)
    get_mock_put(sim_driver.iterations).assert_called_once_with(region.iterations)
    if region.acquisition_mode == AcquisitionMode.SWEPT:
        get_mock_put(sim_driver.energy_step).assert_called_once_with(region.energy_step)


@pytest.mark.parametrize("region", load_i05_mbs_test_xml_seq().regions)
async def test_analyser_sets_region_and_read_configuration_is_correct(
    sim_driver: MbsAnalyserDriverIO[LensMode, PassEnergy],
    region: MbsRegion[LensMode, PassEnergy],
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
            f"{prefix}centre_energy": partial_reading(region.centre_energy),
            f"{prefix}high_energy": partial_reading(region.high_energy),
            f"{prefix}deflector_x": partial_reading(region.deflector_x),
            f"{prefix}energy_step": partial_reading(region.energy_step),
            f"{prefix}pass_energy": partial_reading(region.pass_energy),
            f"{prefix}slices": partial_reading(ANY),
            f"{prefix}iterations": partial_reading(region.iterations),
            f"{prefix}total_steps": partial_reading(ANY),
            f"{prefix}acquire_time": partial_reading(region.acquire_time),
            f"{prefix}acquire_period": partial_reading(ANY),
            f"{prefix}total_time": partial_reading(ANY),
            f"{prefix}energy_axis": partial_reading(ANY),
            f"{prefix}angle_axis": partial_reading(ANY),
            f"{prefix}psu_mode": partial_reading(ANY),
            f"{prefix}dither_steps": partial_reading(0),
            f"{prefix}spin_offset": partial_reading(0),
            f"{prefix}array_size_x": partial_reading(0),
            f"{prefix}array_size_y": partial_reading(0),
            f"{prefix}min_x": partial_reading(0),
            f"{prefix}min_y": partial_reading(0),
            f"{prefix}max_x": partial_reading(0),
            f"{prefix}max_y": partial_reading(0),
        },
    )
