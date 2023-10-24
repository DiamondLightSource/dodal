from asyncio import wait_for
from asyncio.exceptions import TimeoutError

import pytest
import pytest_asyncio
from ophyd_async.core import AsyncStatus, DeviceCollector, set_sim_value

from dodal.devices.xbpm_feedback import XBPMFeedback, XBPMFeedbackI03


@pytest_asyncio.fixture
async def fake_xbpm_feedback_i03():
    async with DeviceCollector(sim=True):
        xbpm_feedback_i03 = XBPMFeedbackI03(prefix="", name="xbpm")

    yield xbpm_feedback_i03


@pytest_asyncio.fixture
async def fake_xbpm_feedback():
    async with DeviceCollector(sim=True):
        xbpm_feedback = XBPMFeedback(prefix="", name="xbpm")

    yield xbpm_feedback


@pytest.mark.asyncio
async def test_given_pos_ok_when_xbpm_feedback_kickoff_then_return_immediately(
    fake_xbpm_feedback: XBPMFeedback,
):
    set_sim_value(fake_xbpm_feedback.pos_ok, 1)
    status = AsyncStatus(fake_xbpm_feedback.trigger())
    await wait_for(status, 0.1)
    assert status.done and status.success


# Same test but for i03 version of device
@pytest.mark.asyncio
async def test_given_pos_stable_when_xbpm_feedback_kickoff_then_return_immediately(
    fake_xbpm_feedback_i03: XBPMFeedbackI03,
):
    set_sim_value(fake_xbpm_feedback_i03.pos_stable, 1)
    status = AsyncStatus(fake_xbpm_feedback_i03.trigger())
    await wait_for(status, 0.1)
    assert status.done and status.success


@pytest.mark.asyncio
async def test_given_pos_not_ok_and_goes_ok_when_xbpm_feedback_kickoff_then_return(
    fake_xbpm_feedback: XBPMFeedback,
):
    set_sim_value(fake_xbpm_feedback.pos_ok, 0)
    status = AsyncStatus(fake_xbpm_feedback.trigger())

    with pytest.raises(TimeoutError):
        await wait_for(status, 0.1)

    assert not status.success
    # Create new status as old one failed
    status = AsyncStatus(fake_xbpm_feedback.trigger())

    set_sim_value(fake_xbpm_feedback.pos_ok, 1)
    await wait_for(status, 0.1)
    assert status.done and status.success


@pytest.mark.asyncio
async def test_given_pos_not_stable_and_goes_stable_when_xbpm_feedback_kickoff_then_return(
    fake_xbpm_feedback_i03: XBPMFeedbackI03,
):
    set_sim_value(fake_xbpm_feedback_i03.pos_stable, 0)
    status = AsyncStatus(fake_xbpm_feedback_i03.trigger())

    with pytest.raises(TimeoutError):
        await wait_for(status, 0.1)

    assert not status.success
    # Create new status as old one failed
    status = AsyncStatus(fake_xbpm_feedback_i03.trigger())

    set_sim_value(fake_xbpm_feedback_i03.pos_stable, 1)
    await wait_for(status, 0.1)
    assert status.done and status.success
