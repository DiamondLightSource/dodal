from unittest.mock import MagicMock, patch

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd.sim import make_fake_device
from ophyd.status import Status

from dodal.devices.xspress3_mini.xspress3_mini import DetectorState, Xspress3Mini


def get_bad_status() -> Status:
    status = Status("get_bad_status")
    status.set_exception(Exception)
    return status


@pytest.fixture
def fake_xspress3mini():
    FakeXspress3Mini = make_fake_device(Xspress3Mini)
    fake_xspress3mini: Xspress3Mini = FakeXspress3Mini(name="xspress3mini")
    return fake_xspress3mini


@pytest.fixture
def status_finished() -> MagicMock:
    return MagicMock()


def test_arm_success_on_busy_state(fake_xspress3mini, status_finished: MagicMock):
    fake_xspress3mini.detector_state.sim_put(DetectorState.ACQUIRE.value)  # type: ignore
    status = fake_xspress3mini.arm()
    status.add_callback(status_finished)
    status_finished.assert_not_called()
    fake_xspress3mini.acquire.sim_put(0)  # type: ignore
    status.wait(timeout=1)


@patch("dodal.devices.xspress3_mini.xspress3_mini.await_value")
def test_stage_in_busy_state(mock_await_value, fake_xspress3mini, RE: RunEngine):
    fake_xspress3mini.detector_state.sim_put(DetectorState.ACQUIRE.value)  # type: ignore
    fake_xspress3mini.acquire.sim_put(0)  # type: ignore
    RE(bps.stage(fake_xspress3mini))


def test_stage_fails_in_failed_acquire_state(fake_xspress3mini, RE: RunEngine):
    with pytest.raises(Exception):
        RE(bps.stage(fake_xspress3mini))
