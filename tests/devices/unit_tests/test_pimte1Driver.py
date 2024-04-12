import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.areadetector.epics.drivers.pimte1_driver import Pimte1Driver

# Long enough for multiple asyncio event loop cycles to run so
# all the tasks have a chance to run
A_BIT = 0.001


@pytest.fixture
async def sim_pimte_driver():
    async with DeviceCollector(sim=True):
        sim_pimte_driver = Pimte1Driver("BLxxI-A-DET-03:CAM")
        # Signals connected here
    yield sim_pimte_driver


async def test_sim_pimte_driver(sim_pimte_driver: Pimte1Driver) -> None:
    assert sim_pimte_driver.name == "sim_pimte_driver"
