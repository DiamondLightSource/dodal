import pytest
from ophyd.sim import make_fake_device

from dodal.devices.xbpm_feedback import XBPMFeedback


@pytest.fixture
def fake_xbpm_feedback():
    FakeXBPMFeedback = make_fake_device(XBPMFeedback)
    return FakeXBPMFeedback(name="xbpm")


def test_given_pos_stable_when_xbpm_feedback_kickoff_then_return_immediately(
    fake_xbpm_feedback: XBPMFeedback,
):
    fake_xbpm_feedback.pos_stable.sim_put(1)
    status = fake_xbpm_feedback.trigger()
    status.wait(0.1)
    assert status.done and status.success


def test_given_pos_not_stable_and_goes_stable_when_xbpm_feedback_kickoff_then_return(
    fake_xbpm_feedback: XBPMFeedback,
):
    fake_xbpm_feedback.pos_stable.sim_put(0)
    status = fake_xbpm_feedback.trigger()

    assert not status.done

    fake_xbpm_feedback.pos_stable.sim_put(1)
    status.wait(0.1)
    assert status.done and status.success
