import asyncio
from unittest.mock import ANY, Mock

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.xspress3.xspress3 import (
    AcquireRBVState,
    DetectorState,
    TriggerMode,
    Xspress3,
)


@pytest.fixture
async def mock_xspress3mini(prefix: str = "BLXX-EA-DET-007:") -> Xspress3:
    async with init_devices(mock=True):
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
    mock_xspress3mini.timeout = 5
    return mock_xspress3mini


async def test_stage_in_RE_success_in_busy_state(
    mock_xspress3mini: Xspress3, RE: RunEngine
):
    # set xspress to busy
    set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.DONE)
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.ACQUIRE)
    # make rbv change from DONE->ACQUIRE->DONE
    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = [AcquireRBVState.ACQUIRE, AcquireRBVState.DONE]
    callback_on_mock_put(
        mock_xspress3mini.acquire,
        lambda *_, **__: set_mock_value(mock_xspress3mini.acquire_rbv, rbv_mocks.get()),
    )
    RE(bps.stage(mock_xspress3mini, wait=True))

    get_mock_put(mock_xspress3mini.trigger_mode).assert_called_once_with(
        TriggerMode.BURST, wait=ANY
    )
    await asyncio.sleep(0.2)
    assert 2 == get_mock_put(mock_xspress3mini.acquire).call_count


async def test_stage_fail_on_detector_not_busy_state(
    mock_xspress3mini: Xspress3, RE: RunEngine
):
    set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.DONE)
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.IDLE)
    mock_xspress3mini.timeout = 0.1
    with pytest.raises(asyncio.TimeoutError):
        await mock_xspress3mini.stage()
    with pytest.raises(FailedStatus):
        RE(bps.stage(mock_xspress3mini, wait=True))
    await asyncio.sleep(0.2)
    assert 2 == get_mock_put(mock_xspress3mini.trigger_mode).call_count
    # unstage is call even when staging failed
    assert 1 == get_mock_put(mock_xspress3mini.acquire).call_count


async def test_stage_fail_to_acquire_timeout(
    mock_xspress3mini: Xspress3, RE: RunEngine
):
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.ACQUIRE)
    set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.DONE)
    mock_xspress3mini.timeout = 0.1
    with pytest.raises(asyncio.TimeoutError):
        await mock_xspress3mini.stage()
    with pytest.raises(FailedStatus):
        RE(bps.stage(mock_xspress3mini, wait=True))
    await asyncio.sleep(0.2)
    assert 2 == get_mock_put(mock_xspress3mini.trigger_mode).call_count
    assert 3 == get_mock_put(mock_xspress3mini.acquire).call_count
