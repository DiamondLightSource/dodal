import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.xbpm_feedback import XBPMFeedback


@pytest.fixture
async def fake_xbpm_feedback() -> XBPMFeedback:
    async with init_devices(mock=True):
        xbpm = XBPMFeedback()
    return xbpm


def test_given_pos_stable_when_xbpm_feedback_kickoff_then_return_immediately(
    RE: RunEngine,
    fake_xbpm_feedback: XBPMFeedback,
):
    set_mock_value(fake_xbpm_feedback.pos_stable, True)

    def plan():
        yield from bps.trigger(fake_xbpm_feedback)
        yield from bps.wait(timeout=0.1)

    RE(plan())


def test_given_pos_not_stable_and_goes_stable_when_xbpm_feedback_kickoff_then_return(
    RE: RunEngine, fake_xbpm_feedback: XBPMFeedback
):
    set_mock_value(fake_xbpm_feedback.pos_stable, False)

    def plan():
        yield from bps.trigger(fake_xbpm_feedback)
        with pytest.raises(expected_exception=TimeoutError):
            yield from bps.wait(timeout=0.1)

        set_mock_value(fake_xbpm_feedback.pos_stable, True)
        yield from bps.wait(0.1)

    RE(plan())
