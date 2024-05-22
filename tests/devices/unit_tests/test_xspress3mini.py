from unittest.mock import MagicMock, patch

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine

from dodal.devices.xspress3_mini.xspress3_mini import DetectorState


def test_arm_success_on_busy_state(mock_xspress3mini):
    status_finished = MagicMock()
    mock_xspress3mini.detector_state.sim_put(DetectorState.ACQUIRE.value)  # type: ignore
    status = mock_xspress3mini.arm()
    status.add_callback(status_finished)
    status_finished.assert_not_called()
    mock_xspress3mini.acquire.sim_put(0)  # type: ignore
    status.wait(timeout=1)


@patch("dodal.devices.xspress3_mini.xspress3_mini.await_value")
def test_stage_in_busy_state(mock_await_value, mock_xspress3mini, RE: RunEngine):
    mock_xspress3mini.detector_state.sim_put(DetectorState.ACQUIRE.value)  # type: ignore
    mock_xspress3mini.acquire.sim_put(0)  # type: ignore
    RE(bps.stage(mock_xspress3mini))


def test_stage_fails_in_failed_acquire_state(mock_xspress3mini, RE: RunEngine):
    with pytest.raises(Exception):
        RE(bps.stage(mock_xspress3mini))
