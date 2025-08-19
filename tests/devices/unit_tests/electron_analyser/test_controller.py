import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import SignalR, init_devices

import dodal.devices.b07 as b07
import dodal.devices.i09 as i09
from dodal.devices.electron_analyser import ElectronAnalyserController
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.vgscienta import VGScientaAnalyserDriverIO
from dodal.testing.electron_analyser import create_driver


@pytest.fixture(
    params=[
        VGScientaAnalyserDriverIO[i09.LensMode, i09.PsuMode, i09.PassEnergy],
        SpecsAnalyserDriverIO[b07.LensMode, b07.PsuMode],
    ]
)
async def sim_driver(
    request: pytest.FixtureRequest,
    energy_sources: dict[str, SignalR[float]],
    RE: RunEngine,
) -> AbstractAnalyserDriverIO:
    async with init_devices(mock=True):
        sim_driver = await create_driver(
            request.param, prefix="TEST:", energy_sources=energy_sources
        )
    return sim_driver


@pytest.fixture
async def controller(
    sim_driver: AbstractAnalyserDriverIO,
) -> ElectronAnalyserController:
    return ElectronAnalyserController(sim_driver)


def test_controller_deadtime(
    controller: ElectronAnalyserController,
) -> None:
    assert controller.get_deadtime(None) == 0
