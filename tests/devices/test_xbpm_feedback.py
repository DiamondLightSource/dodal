import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.xbpm_feedback import XBPMFeedback


@pytest.fixture
async def fake_xbpm_feedback() -> XBPMFeedback:
    async with init_devices(mock=True):
        xbpm_feedback = XBPMFeedback("")
    return xbpm_feedback


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


@pytest.mark.parametrize(
    "time_before_stable, expected_log_messages",
    [
        (1.1, 3),
        (30, 8),
        (260, 12),
        (10900, 23),
    ],
)
@patch("dodal.common.device_utils.sleep")
def test_logging_while_waiting_for_XBPM(
    asyncio_sleep: AsyncMock,
    time_before_stable: float,
    expected_log_messages: int,
    RE: RunEngine,
    fake_xbpm_feedback: XBPMFeedback,
    caplog,
):
    set_mock_value(fake_xbpm_feedback.pos_stable, False)

    current_sleep_time = 0

    async def go_stable_after_a_number_of_sleep_calls(*args, **kwargs):
        nonlocal current_sleep_time
        if current_sleep_time >= time_before_stable:
            set_mock_value(fake_xbpm_feedback.pos_stable, True)
            await asyncio.sleep(0)
        current_sleep_time += args[0]

    asyncio_sleep.side_effect = go_stable_after_a_number_of_sleep_calls

    with caplog.at_level("INFO"):
        RE(bps.trigger(fake_xbpm_feedback, wait=True))

    log_messages = sum(
        record.getMessage() == "Waiting for XBPM" for record in caplog.records
    )
    assert log_messages == expected_log_messages
