import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd.sim import make_fake_device

from dodal.devices.xspress3_mini.xspress3_mini import DetectorState, Xspress3Mini


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


def test_stage_in_busy_state(fake_xspress3mini):
    fake_xspress3mini.detector_state.sim_put(DetectorState.ACQUIRE.value)
    RE = RunEngine()
    RE(bps.stage(fake_xspress3mini))
    fake_xspress3mini.acquire_status.wait(timeout=5)
