import asyncio
import pytest

from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector

from dodal.devices.bimorph_mirror import BimorphMirror

@pytest.fixture
def mirror(RE: RunEngine) -> BimorphMirror:
    with DeviceCollector(mock=True):
        bm = BimorphMirror(prefix="BL02J-EA-IOC-97:G0:", number_of_channels=8)
    
    return bm


async def test_set_channels(mirror: BimorphMirror):
    value = {2:50.0, 8:24.0}

    await mirror.set(value)

    assert (await mirror.channels[2].vout.get_value()) == 50.0
    assert (await mirror.channels[8].vout.get_value()) == 24.0
