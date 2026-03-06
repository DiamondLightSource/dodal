import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import WatchableAsyncStatus, init_devices, set_mock_value

from dodal.devices.baton import Baton
from dodal.devices.xbpm_feedback import XBPMFeedback


@pytest.fixture
async def fake_xbpm_feedback() -> XBPMFeedback:
    async with init_devices(mock=True):
        baton = Baton("BATON-01:")
        xbpm_feedback = XBPMFeedback("", baton=baton, name="xbpm_feedback")
    return xbpm_feedback


@pytest.fixture
def xbpm_feedback_in_commissioning_mode(
    fake_xbpm_feedback,
) -> Generator[XBPMFeedback, None, None]:
    set_mock_value(fake_xbpm_feedback.baton_ref().commissioning, True)  # type: ignore
    yield fake_xbpm_feedback


def test_given_pos_stable_when_xbpm_feedback_kickoff_then_return_immediately(
    run_engine: RunEngine,
    fake_xbpm_feedback: XBPMFeedback,
):
    set_mock_value(fake_xbpm_feedback.pos_stable, True)

    def plan():
        yield from bps.trigger(fake_xbpm_feedback)
        yield from bps.wait(timeout=0.1)

    run_engine(plan())


def test_given_pos_not_stable_and_goes_stable_when_xbpm_feedback_kickoff_then_return(
    run_engine: RunEngine, fake_xbpm_feedback: XBPMFeedback
):
    set_mock_value(fake_xbpm_feedback.pos_stable, False)

    def plan():
        yield from bps.trigger(fake_xbpm_feedback)
        with pytest.raises(expected_exception=TimeoutError):
            yield from bps.wait(timeout=0.1)

        set_mock_value(fake_xbpm_feedback.pos_stable, True)
        yield from bps.wait(0.1)

    run_engine(plan())


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
def test_logging_while_waiting_for_xbpm(
    asyncio_sleep: AsyncMock,
    time_before_stable: float,
    expected_log_messages: int,
    run_engine: RunEngine,
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
        run_engine(bps.trigger(fake_xbpm_feedback, wait=True))

    log_messages = sum(
        record.getMessage() == "Waiting for XBPM" for record in caplog.records
    )
    assert log_messages == expected_log_messages


@patch("dodal.devices.xbpm_feedback.observe_value")
@patch("dodal.devices.xbpm_feedback.periodic_reminder")
def test_xbpm_feedback_does_not_wait_if_commissioning_mode_enabled(
    mock_periodic_reminder: AsyncMock,
    mock_observe_value: AsyncMock,
    xbpm_feedback_in_commissioning_mode: XBPMFeedback,
    run_engine: RunEngine,
):
    set_mock_value(xbpm_feedback_in_commissioning_mode.pos_stable, False)
    run_engine(bps.trigger(xbpm_feedback_in_commissioning_mode, wait=True))
    mock_periodic_reminder.assert_not_called()
    mock_observe_value.assert_not_called()


async def test_xbpm_feedback_trigger_is_watchable(
    fake_xbpm_feedback: XBPMFeedback,
    run_engine: RunEngine,
):
    set_mock_value(fake_xbpm_feedback.pos_stable, False)
    received_events = []

    def on_event(**kwargs):
        received_events.append(kwargs)
        if kwargs.get("current") == 0:
            set_mock_value(fake_xbpm_feedback.pos_stable, True)

    def wait_for_feedback():
        status = yield from bps.trigger(fake_xbpm_feedback, wait=False)
        assert isinstance(status, WatchableAsyncStatus)
        status.watch(on_event)  # type: ignore
        yield from bps.wait(timeout=1)

    run_engine(wait_for_feedback())

    assert received_events[0]["name"] == "xbpm_feedback-pos_stable"
    assert received_events[0]["current"] == 0
    assert received_events[0]["initial"] == 0
    assert received_events[0]["target"] == 1
    assert received_events[1]["name"] == "xbpm_feedback-pos_stable"
    assert received_events[1]["current"] == 1
    assert received_events[1]["initial"] == 0
    assert received_events[1]["target"] == 1
