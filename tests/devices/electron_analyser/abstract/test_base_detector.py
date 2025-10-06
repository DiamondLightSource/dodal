from unittest.mock import AsyncMock

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    set_mock_value,
)

import dodal.devices.b07 as b07
import dodal.devices.i09 as i09
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    BaseElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.energy_sources import EnergySource
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.testing.electron_analyser import create_detector


@pytest.fixture(
    params=[
        VGScientaDetector[i09.LensMode, i09.PsuMode, i09.PassEnergy],
        SpecsDetector[b07.LensMode, b07.PsuMode],
    ]
)
async def sim_detector(
    request: pytest.FixtureRequest,
    single_energy_source: EnergySource,
    RE: RunEngine,
) -> BaseElectronAnalyserDetector[AbstractAnalyserDriverIO]:
    async with init_devices(mock=True):
        sim_detector = await create_detector(
            request.param,
            prefix="TEST:",
            energy_source=single_energy_source,
        )
    # Needed for specs so we don't get division by zero error.
    set_mock_value(sim_detector.driver.slices, 1)
    return sim_detector


def test_analyser_detector_trigger(
    sim_detector: BaseElectronAnalyserDetector[AbstractAnalyserDriverIO],
    RE: RunEngine,
) -> None:
    sim_detector._controller.arm = AsyncMock()
    sim_detector._controller.wait_for_idle = AsyncMock()

    RE(bps.trigger(sim_detector), wait=True)

    sim_detector._controller.arm.assert_awaited_once()
    sim_detector._controller.wait_for_idle.assert_awaited_once()


async def test_analyser_detector_read(
    sim_detector: BaseElectronAnalyserDetector[AbstractAnalyserDriverIO],
) -> None:
    driver_read = await sim_detector._controller.driver.read()
    await assert_reading(sim_detector, driver_read)


async def test_analyser_describe(
    sim_detector: BaseElectronAnalyserDetector[AbstractAnalyserDriverIO],
) -> None:
    energy_array = await sim_detector._controller.driver.energy_axis.get_value()
    angle_array = await sim_detector._controller.driver.angle_axis.get_value()
    data = await sim_detector.describe()
    assert data[f"{sim_detector._controller.driver.image.name}"]["shape"] == [
        len(angle_array),
        len(energy_array),
    ]


async def test_analyser_detector_configuration(
    sim_detector: BaseElectronAnalyserDetector[AbstractAnalyserDriverIO],
) -> None:
    driver_config = await sim_detector._controller.driver.read_configuration()
    await assert_configuration(sim_detector, driver_config)


async def test_analyser_detector_describe_configuration(
    sim_detector: BaseElectronAnalyserDetector[AbstractAnalyserDriverIO],
) -> None:
    driver_describe_config = (
        await sim_detector._controller.driver.describe_configuration()
    )

    assert await sim_detector.describe_configuration() == driver_describe_config
