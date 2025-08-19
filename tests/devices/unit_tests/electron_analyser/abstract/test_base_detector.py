from unittest.mock import AsyncMock

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import SignalR, init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    set_mock_value,
)

import dodal.devices.i09 as i09
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.testing.electron_analyser import create_detector


@pytest.fixture(VGScientaDetector[i09.LensMode, i09.PsuMode, i09.PassEnergy])
async def sim_detector(
    request: pytest.FixtureRequest,
    energy_sources: dict[str, SignalR[float]],
    RE: RunEngine,
) -> AbstractElectronAnalyserDetector[AbstractAnalyserDriverIO]:
    async with init_devices(mock=True):
        sim_detector = await create_detector(
            request.param,
            prefix="TEST:",
            energy_sources=energy_sources,
        )
    return sim_detector


def test_analyser_detector_trigger(
    sim_detector: AbstractElectronAnalyserDetector[AbstractAnalyserDriverIO],
    RE: RunEngine,
) -> None:
    sim_detector.controller.arm = AsyncMock()
    sim_detector.controller.wait_for_idle = AsyncMock()

    RE(bps.trigger(sim_detector), wait=True)

    sim_detector.controller.arm.assert_awaited_once()
    sim_detector.controller.wait_for_idle.assert_awaited_once()


async def test_analyser_detector_read(
    sim_detector: AbstractElectronAnalyserDetector[AbstractAnalyserDriverIO],
) -> None:
    driver = sim_detector.driver
    driver_read = await driver.read()
    await assert_reading(sim_detector, driver_read)


async def test_analyser_describe(
    sim_detector: AbstractElectronAnalyserDetector[AbstractAnalyserDriverIO],
) -> None:
    energy_array = np.array([0, 0, 0, 0], dtype=np.float64)
    angle_array = np.array([0, 0], dtype=np.float64)

    set_mock_value(sim_detector.driver.energy_axis, energy_array)
    set_mock_value(sim_detector.driver.angle_axis, angle_array)

    data = await sim_detector.describe()
    assert data[f"{sim_detector.name}-_driver-image"]["shape"] == [
        len(angle_array),
        len(energy_array),
    ]


async def test_analyser_detector_configuration(
    sim_detector: AbstractElectronAnalyserDetector[AbstractAnalyserDriverIO],
) -> None:
    driver = sim_detector.driver
    driver_config = await driver.read_configuration()
    # Type ignore needed until this is in next release
    # https://github.com/bluesky/ophyd-async/issues/1013#event-19205466589
    await assert_configuration(sim_detector, driver_config)  # type: ignore


async def test_analyser_detector_describe_configuration(
    sim_detector: AbstractElectronAnalyserDetector[AbstractAnalyserDriverIO],
) -> None:
    driver = sim_detector.driver
    driver_describe_config = await driver.describe_configuration()

    assert await sim_detector.describe_configuration() == driver_describe_config
