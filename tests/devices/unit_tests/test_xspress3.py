import asyncio

import pytest
from ophyd_async.core import DeviceCollector, set_sim_value

from dodal.devices.xspress3.xspress3 import (
    AcquireState,
    DetectorState,
    Xspress3Mini,
)


@pytest.fixture
async def fake_xspress3mini(prefix: str = "BLXX-EA-DET-007:") -> Xspress3Mini:
    async with DeviceCollector(sim=True):
        fake_xspress3mini = Xspress3Mini(prefix, "Xspress3Mini", 2)
    assert fake_xspress3mini.channels[1].name == "Xspress3Mini-channels-1"
    assert fake_xspress3mini.channels[2].name == "Xspress3Mini-channels-2"

    return fake_xspress3mini


async def test_arm_success_on_busy_state_OA(fake_xspress3mini: Xspress3Mini):
    set_sim_value(fake_xspress3mini.detector_state, DetectorState.ACQUIRE)
    status = await fake_xspress3mini.stage()
    assert status.done is False
    set_sim_value(fake_xspress3mini.acquire, AcquireState.DONE)
    await asyncio.sleep(0.1)
    assert status.done is True


async def test_arm_fail_on_not_busy_state(fake_xspress3mini: Xspress3Mini):
    set_sim_value(fake_xspress3mini.detector_state, DetectorState.IDLE)
    with pytest.raises(TimeoutError):
        await fake_xspress3mini.stage()
