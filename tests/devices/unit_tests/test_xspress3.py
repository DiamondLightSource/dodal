from unittest.mock import ANY

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.xspress3.xspress3 import (
    AcquireRBVState,
    AcquireState,
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
    mock_xspress3mini.timeout = 0.1
    return mock_xspress3mini


async def test_stage_success_on_busy_state(mock_xspress3mini: Xspress3):
    set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.DONE)
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.ACQUIRE)

    callback_on_mock_put(
        mock_xspress3mini.acquire,
        lambda *_, **__: set_mock_value(
            mock_xspress3mini.acquire_rbv, AcquireRBVState.ACQUIRE
        ),
    )

    await mock_xspress3mini.stage()
    get_mock_put(mock_xspress3mini.trigger_mode).assert_called_once_with(
        TriggerMode.BURST, wait=ANY, timeout=ANY
    )
    get_mock_put(mock_xspress3mini.acquire).assert_called_once_with(
        AcquireState.ACQUIRE, wait=ANY, timeout=ANY
    )


async def test_stage_fail_on_detector_not_busy_state(mock_xspress3mini: Xspress3):
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.IDLE)
    with pytest.raises(TimeoutError):
        await mock_xspress3mini.stage()


async def test_stage_fail_to_acquire_timeout(mock_xspress3mini: Xspress3):
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.ACQUIRE)
    set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.DONE)
    with pytest.raises(TimeoutError):
        await mock_xspress3mini.stage()


def test_stage_timeOut_in_RE(mock_xspress3mini: Xspress3, RE: RunEngine):
    with pytest.raises(Exception):
        RE(bps.stage(mock_xspress3mini, wait=True))


def stage_plan(mock_xspress3mini: Xspress3):
    callback_on_mock_put(
        mock_xspress3mini.acquire,
        lambda *_, **__: set_mock_value(
            mock_xspress3mini.acquire_rbv, AcquireRBVState.ACQUIRE
        ),
    )
    yield from bps.stage(mock_xspress3mini, group="aa", wait=True)
    callback_on_mock_put(
        mock_xspress3mini.acquire,
        lambda *_, **__: set_mock_value(
            mock_xspress3mini.acquire_rbv, AcquireRBVState.DONE
        ),
    )
    yield from bps.unstage(mock_xspress3mini, wait=True)


def test_stage_in_RE(mock_xspress3mini: Xspress3, RE: RunEngine):
    set_mock_value(mock_xspress3mini.acquire_rbv, AcquireRBVState.DONE)
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.ACQUIRE)
    RE(stage_plan(mock_xspress3mini))

    get_mock_put(mock_xspress3mini.trigger_mode).assert_called_once_with(
        TriggerMode.BURST, wait=ANY, timeout=ANY
    )
    assert get_mock_put(mock_xspress3mini.acquire).call_count == 2
