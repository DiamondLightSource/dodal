from unittest.mock import AsyncMock, call, patch

import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.waittime import WaitTime


@pytest.fixture
def waittime() -> WaitTime:
    with init_devices(mock=True):
        waittime = WaitTime()
    return waittime


@patch("asyncio.sleep")
@pytest.mark.parametrize("time", [1, 0.2])
async def test_waittime_waits_for_set_time_on_set(
    sleep: AsyncMock, waittime: WaitTime, time: float
):
    await waittime.set(time)
    sleep.assert_awaited_once_with(time)


@patch("asyncio.sleep")
@pytest.mark.parametrize("time", [1, 0.2])
async def test_waittime_waits_for_set_time_on_trigger(
    sleep: AsyncMock, waittime: WaitTime, time: float
):
    await waittime.set(time)
    await waittime.trigger()
    sleep.assert_has_awaits([call(time), call(time)])


@patch("asyncio.sleep")
@pytest.mark.parametrize("time", [1, 0.2])
async def test_waittime_read(sleep: AsyncMock, waittime: WaitTime, time: float):
    set_mock_value(waittime.time_to_wait, time)
    await assert_reading(
        waittime,
        {
            "waittime-time_to_wait": partial_reading(time),
        },
    )
