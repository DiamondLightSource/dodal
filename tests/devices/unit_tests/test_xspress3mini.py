from unittest.mock import MagicMock

import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd.sim import make_fake_device
from ophyd.status import Status
from ophyd.utils.errors import WaitTimeoutError

from dodal.devices.xspress3_mini.xspress3_mini import DetectorState, Xspress3Mini


def get_good_status() -> Status:
    status = Status()
    status.set_finished()
    return status


def get_bad_status() -> Status:
    status = Status()
    status.set_exception(Exception)
    return status


@pytest.fixture
def fake_xspress3mini():
    FakeXspress3Mini: Xspress3Mini = make_fake_device(Xspress3Mini)
    fake_xspress3mini: Xspress3Mini = FakeXspress3Mini(name="xspress3mini")
    return fake_xspress3mini


def test_arm_success_on_busy_state(fake_xspress3mini):
    fake_xspress3mini.detector_state.sim_put(DetectorState.IDLE.value)
    status = fake_xspress3mini.arm()
    assert status.done is False
    fake_xspress3mini.detector_state.sim_put(DetectorState.ACQUIRE.value)
    status.wait(timeout=1)
    fake_xspress3mini.acquire_status.wait(timeout=1)


def test_stage_in_busy_state(fake_xspress3mini):
    fake_xspress3mini.detector_state.sim_put(DetectorState.ACQUIRE.value)
    RE = RunEngine()
    RE(bps.stage(fake_xspress3mini))
    fake_xspress3mini.acquire_status.wait(timeout=1)


def test_stage_fails_in_failed_acquire_state(fake_xspress3mini):
    bad_status = Status()
    bad_status.set_exception(Exception)
    RE = RunEngine()
    fake_xspress3mini.do_start = MagicMock(return_value=get_good_status())
    fake_xspress3mini.acquire_status = get_bad_status()
    with pytest.raises(Exception):
        RE(bps.stage(fake_xspress3mini))
