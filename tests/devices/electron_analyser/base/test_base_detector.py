from unittest.mock import AsyncMock

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
)

import dodal.devices.b07 as b07
import dodal.devices.i09 as i09
from dodal.devices.electron_analyser.base import (
    EnergySource,
    GenericElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.base.energy_sources import EnergySource
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.testing.electron_analyser import create_detector
from tests.devices.electron_analyser.helper_util import get_test_sequence


@pytest.fixture(
    params=[
        VGScientaDetector[i09.LensMode, i09.PsuMode, i09.PassEnergy],
        SpecsDetector[b07.LensMode, b07.PsuMode],
    ]
)
async def sim_detector(
    request: pytest.FixtureRequest,
    single_energy_source: EnergySource,
) -> GenericElectronAnalyserDetector:
    async with init_devices(mock=True):
        sim_detector = create_detector(
            request.param,
            prefix="TEST:",
            energy_source=single_energy_source,
        )
    # Needed for specs so we don't get division by zero error.
    set_mock_value(sim_detector.driver.slices, 1)
    return sim_detector


def test_base_analyser_detector_trigger(
    sim_detector: GenericElectronAnalyserDetector,
    run_engine: RunEngine,
) -> None:
    sim_detector._controller.arm = AsyncMock()
    sim_detector._controller.wait_for_idle = AsyncMock()

    run_engine(bps.trigger(sim_detector, wait=True), wait=True)

    sim_detector._controller.arm.assert_awaited_once()
    sim_detector._controller.wait_for_idle.assert_awaited_once()


async def test_base_analyser_detector_read(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    driver_read = await sim_detector._controller.driver.read()
    await assert_reading(sim_detector, driver_read)


async def test_base_analyser_describe(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    energy_array = await sim_detector._controller.driver.energy_axis.get_value()
    angle_array = await sim_detector._controller.driver.angle_axis.get_value()
    data = await sim_detector.describe()
    assert data[f"{sim_detector._controller.driver.image.name}"]["shape"] == [
        len(angle_array),
        len(energy_array),
    ]


async def test_base_analyser_detector_configuration(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    driver_config = await sim_detector._controller.driver.read_configuration()
    await assert_configuration(sim_detector, driver_config)


async def test_base_analyser_detector_describe_configuration(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    driver_describe_config = (
        await sim_detector._controller.driver.describe_configuration()
    )

    assert await sim_detector.describe_configuration() == driver_describe_config


async def test_analyser_detector_stage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector._controller.disarm = AsyncMock()

    await sim_detector.stage()

    sim_detector._controller.disarm.assert_awaited_once()


async def test_analyser_detector_unstage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector._controller.disarm = AsyncMock()

    await sim_detector.unstage()

    sim_detector._controller.disarm.assert_awaited_once()


def test_analyser_detector_trigger_called_controller_prepare(
    sim_detector: GenericElectronAnalyserDetector,
    run_engine: RunEngine,
) -> None:
    sim_detector._controller.prepare = AsyncMock()
    sim_detector._controller.arm = AsyncMock()
    sim_detector._controller.wait_for_idle = AsyncMock()

    run_engine(bps.trigger(sim_detector, wait=True), wait=True)

    sim_detector._controller.prepare.assert_awaited_once()
    sim_detector._controller.arm.assert_awaited_once()
    sim_detector._controller.wait_for_idle.assert_awaited_once()


def test_analyser_detector_set_called_controller_setup_with_region(
    sim_detector: GenericElectronAnalyserDetector,
    run_engine: RunEngine,
) -> None:
    seq = sim_detector.sequence_loader.load(get_test_sequence(type(sim_detector)))
    region = seq.get_enabled_regions()[0]
    sim_detector._controller.setup_with_region = AsyncMock()
    run_engine(bps.mv(sim_detector, region), wait=True)
    sim_detector._controller.setup_with_region.assert_awaited_once_with(region)
