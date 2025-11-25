import pytest
from ophyd_async.core import init_devices

from dodal.devices.i04.transfocator import Transfocator


@pytest.fixture
async def fake_transfocator() -> Transfocator:
    async with init_devices(mock=True):
        transfocator = Transfocator(prefix="", name="transfocator")
    return transfocator
