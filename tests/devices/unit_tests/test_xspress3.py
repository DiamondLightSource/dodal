import asyncio
from unittest.mock import AsyncMock

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, callback_on_mock_put, set_mock_value

from dodal.devices.xspress3.xspress3 import (
    AcquireRBVState,
    AcquireState,
    AsyncStatus,
    DetectorState,
    TriggerMode,
    Xspress3,
)


@pytest.fixture
async def mock_xspress3mini(prefix: str = "BLXX-EA-DET-007:") -> Xspress3:
    async with DeviceCollector(mock=True):
        mock_xspress3mini = Xspress3(prefix, "Xspress3Mini", 2)
    assert mock_xspress3mini.channels[1].name == "Xspress3Mini-channels-1"
    assert mock_xspress3mini.channels[2].name == "Xspress3Mini-channels-2"
    assert (
        mock_xspress3mini.get_roi_calc_status[1].name
        == "Xspress3Mini-get_roi_calc_status-1"
    )
    assert (
        mock_xspress3mini.get_roi_calc_status[2].name
        == "Xspress3Mini-get_roi_calc_status-2"
    )
    assert mock_xspress3mini.roi_mca[1].name == "Xspress3Mini-roi_mca-1"
    assert mock_xspress3mini.roi_mca[2].name == "Xspress3Mini-roi_mca-2"
    mock_xspress3mini.timeout = 0.5
    return mock_xspress3mini


async def test_stage_success_on_busy_state(mock_xspress3mini: Xspress3):
    set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.DONE)
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.ACQUIRE)

    callback_on_mock_put(
        mock_xspress3mini.acquire,
        set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.ACQUIRE),
    )

    mock_xspress3mini.trigger_mode.set = AsyncMock()
    mock_xspress3mini.acquire.set = AsyncMock()
    status: AsyncStatus = mock_xspress3mini.stage()
    assert status.done is False
    await asyncio.sleep(0.01)
    set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.DONE)
    await asyncio.sleep(0.01)
    assert status.done is True
    mock_xspress3mini.trigger_mode.set.assert_called_once_with(TriggerMode.BURST)
    mock_xspress3mini.acquire.set.assert_called_once_with(AcquireState.ACQUIRE)


async def test_stage_fail_on_not_busy_state(mock_xspress3mini: Xspress3):
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.IDLE)
    with pytest.raises(TimeoutError):
        await mock_xspress3mini.stage()


async def test_stage_fail_timeout(mock_xspress3mini: Xspress3):
    set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.ACQUIRE)
    with pytest.raises(TimeoutError):
        await mock_xspress3mini.stage()
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.IDLE)
    with pytest.raises(TimeoutError):
        await mock_xspress3mini.stage()

def test_stage_timeOut_in_RE(mock_xspress3mini: Xspress3, RE: RunEngine):
    with pytest.raises(Exception):
        RE(bps.stage(mock_xspress3mini, wait=True))