import asyncio

import pytest
from ophyd_async.core import DeviceCollector, set_mock_value

from dodal.devices.xspress3.xspress3 import (
    AcquireState,
    DetectorState,
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

    return mock_xspress3mini


async def test_arm_success_on_busy_state(mock_xspress3mini: Xspress3):
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.ACQUIRE)
    status = await mock_xspress3mini.stage()
    assert status.done is False
    set_mock_value(mock_xspress3mini.acquire, AcquireState.DONE)
    await asyncio.sleep(0.1)
    assert status.done is True


async def test_arm_fail_on_not_busy_state(mock_xspress3mini: Xspress3):
    set_mock_value(mock_xspress3mini.detector_state, DetectorState.IDLE)
    with pytest.raises(TimeoutError):
        await mock_xspress3mini.stage()
