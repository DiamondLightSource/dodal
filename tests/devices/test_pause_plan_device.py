import asyncio

import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import InOut, SignalRW, init_devices, soft_signal_rw

from dodal.devices.fast_shutter import GenericFastShutter
from dodal.devices.pause_plan_device import PausePlanDevice


@pytest.fixture
def shutter() -> GenericFastShutter:
    with init_devices(mock=True):
        shutter = GenericFastShutter(
            "TEST:", open_state=InOut.OUT, close_state=InOut.IN
        )
    return shutter


@pytest.fixture
def sig1() -> SignalRW[int]:
    with init_devices(mock=True):
        sig1 = soft_signal_rw(int, initial_value=0)
    return sig1


@pytest.fixture
def sig2() -> SignalRW[int]:
    with init_devices(mock=True):
        sig2 = soft_signal_rw(int, initial_value=0)
    return sig2


@pytest.fixture
async def pause_plan_device(
    sig1: SignalRW[float],
    sig2: SignalRW[float],
    shutter: GenericFastShutter,
) -> PausePlanDevice:

    async def _close_shutter():
        await shutter.set(shutter.close_state)

    async def _open_shutter():
        await shutter.set(shutter.open_state)

    with init_devices(mock=True):
        pause_plan_device = PausePlanDevice(
            {
                sig1: lambda v: v == 1,
                sig2: lambda v: v > 5,
            },
            callable_when_paused=_close_shutter,
            callable_on_resume=_open_shutter,
            seconds_to_wait_before_resume=0,
        )
    return pause_plan_device


async def test_conditions_can_arrive_in_any_order(
    pause_plan_device: PausePlanDevice,
    sig1: SignalRW[float],
    sig2: SignalRW[float],
    shutter: GenericFastShutter,
):
    await shutter.set(shutter.open_state)

    status = pause_plan_device.stage()

    await asyncio.sleep(0.1)

    assert not status.done
    assert await shutter.shutter_state.get_value() == shutter.close_state

    await sig1.set(1)
    await sig2.set(10)

    await status
    assert status.success
    assert await shutter.shutter_state.get_value() == shutter.open_state


@pytest.mark.asyncio
async def test_conditions_already_met(
    pause_plan_device: PausePlanDevice, sig1: SignalRW[float], sig2: SignalRW[float]
):
    await sig1.set(1)
    await sig2.set(10)

    status = pause_plan_device.stage()

    await status

    assert status.success


async def test_pause_device_blocks_plan_until_conditions_met(
    run_engine: RunEngine,
    pause_plan_device: PausePlanDevice,
    sig1: SignalRW[float],
    sig2: SignalRW[float],
):

    start = asyncio.Event()

    async def update_signals():
        await start.wait()
        await sig1.set(1)
        await sig2.set(6)

    asyncio.create_task(update_signals())

    def plan():
        start.set()
        yield from bps.stage(pause_plan_device)
        yield from bps.null()

    run_engine(plan())
