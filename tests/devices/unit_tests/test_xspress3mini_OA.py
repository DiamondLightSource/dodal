import asyncio

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd.status import Status
from ophyd_async.core import DeviceCollector, set_sim_value

from dodal.devices.ophyd_async_xspress3_mini.xspress3_mini_oa import (
    AcquireState,
    DetectorState,
    Xspress3Mini,
)


def get_bad_status() -> Status:
    status = Status("get_bad_status")
    status.set_exception(Exception)
    return status


@pytest.fixture
async def fake_xspress3mini(prefix: str = "huh") -> Xspress3Mini:
    async with DeviceCollector(sim=True):
        fake_xspress3mini = Xspress3Mini(prefix, "Xspress3Mini")
    return fake_xspress3mini


async def test_arm_success_on_busy_state_OA(fake_xspress3mini: Xspress3Mini):
    # set_sim_value(fake_xspress3mini.detector_state,DetectorState.IDLE)
    set_sim_value(fake_xspress3mini.detector_state, DetectorState.ACQUIRE)
    status = await fake_xspress3mini.arm()
    assert status.done is False
    set_sim_value(fake_xspress3mini.acquire, AcquireState.DONE)
    await asyncio.sleep(0.1)
    assert status.done is True
    await fake_xspress3mini.stage()


# @patch("dodal.devices.xspress3_mini.xspress3_mini.await_value")
def test_stage_in_busy_state_OA(fake_xspress3mini: Xspress3Mini, RE: RunEngine):
    # set_sim_value(fake_xspress3mini.detector_state,DetectorState.ACQUIRE)
    # set_sim_value(fake_xspress3mini.acquire, AcquireState.DONE)
    RE(bps.stage(fake_xspress3mini))


"""
def test_stage_fails_in_failed_acquire_state(fake_xspress3mini: Xspress3Mini, RE: RunEngine):
    set_sim_value(fake_xspress3mini.detector_state,DetectorState.IDLE)
    with pytest.raises(Exception):
        RE(bps.stage(fake_xspress3mini))
"""
