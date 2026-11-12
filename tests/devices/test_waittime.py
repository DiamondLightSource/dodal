import math
import time

import pytest

from dodal.devices.waittime import WaitTime


from unittest.mock import patch, AsyncMock
from ophyd_async.core import init_devices

@pytest.fixture
def waittime() -> WaitTime:
     with init_devices(mock=True):
          waittime = WaitTime()
     return waittime

@patch("asyncio.sleep")
@pytest.mark.parametrize("time", [1, 0.2])
async def test_waittime_waits_for_set_time_on_set(waittime: WaitTime, sleep: AsyncMock, time: float):
    await under_test.set(test_time)
    sleep.assert_awaited_once_with(test_time)


from unittest.mock import call

@patch("asyncio.sleep")
@pytest.mark.parametrize("time", [1, 0.2])
async def test_waittime_waits_for_set_time_on_trigger(waittime: WaitTime, sleep: AsyncMock, time: float):
    await waittime.set(time)
    await waittime.trigger()
    sleep.assert_has_awaits([call(time), call(time)])
