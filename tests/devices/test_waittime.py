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


@pytest.mark.timeout(5)
@pytest.mark.parametrize(
    "test_time",
    [1, 0.2],
)
async def test_waittime_waits_for_set_time_on_trigger(test_time: int):
    under_test = WaitTime()
    await under_test.set(test_time)

    start_time = time.time()
    await under_test.trigger()
    time_taken = time.time() - start_time

    assert math.isclose(time_taken, test_time, abs_tol=0.01)
