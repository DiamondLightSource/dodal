import asyncio
from unittest.mock import ANY, AsyncMock, call, patch

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import get_mock_put

from dodal.devices.thawer import Thawer, ThawerStates, ThawingException, ThawingTimer


@pytest.fixture
def thawer(RE):
    with init_devices(mock=True):
        thawer = Thawer("", name="thawer")
    return thawer


def patch_sleep(mocked_sleep: AsyncMock):
    release_sleep = asyncio.Event()

    async def mock_sleep_func(_):
        await release_sleep.wait()

    mocked_sleep.side_effect = mock_sleep_func
    return release_sleep


@patch("dodal.devices.thawer.sleep", new_callable=AsyncMock)
async def test_when_thawing_triggered_then_turn_on_sleep_and_turn_off(
    mock_sleep: AsyncMock,
    thawer: Thawer,
):
    release_sleep = patch_sleep(mock_sleep)
    mock_thawer_control = get_mock_put(thawer.control)

    triggering_status = thawer.thaw_for_time_s.set(10)

    await asyncio.sleep(0.01)
    mock_thawer_control.assert_called_once_with(ThawerStates.ON, wait=ANY)
    mock_sleep.assert_called_once_with(10)
    mock_sleep.assert_awaited_once()
    mock_thawer_control.reset_mock()
    release_sleep.set()
    await asyncio.sleep(0.01)
    mock_thawer_control.assert_called_once_with(ThawerStates.OFF, wait=ANY)
    assert triggering_status.done


@patch("dodal.devices.thawer.sleep")
async def test_given_thawing_already_triggered_when_triggered_again_then_fails(
    mock_sleep: AsyncMock,
    thawer: Thawer,
):
    release_sleep = patch_sleep(mock_sleep)

    status = thawer.thaw_for_time_s.set(10)

    try:
        await asyncio.sleep(0.01)

        with pytest.raises(ThawingException):
            await thawer.thaw_for_time_s.set(10)
    finally:
        release_sleep.set()
        await status


@patch("dodal.devices.thawer.sleep")
async def test_given_thawing_already_triggered_when_stop_called_then_stop_thawing(
    mock_sleep: AsyncMock,
    thawer: Thawer,
):
    patch_sleep(mock_sleep)
    mock_thawer_control = get_mock_put(thawer.control)

    thawing_status = thawer.thaw_for_time_s.set(10)
    await asyncio.sleep(0.01)

    await thawer.stop()

    with pytest.raises(asyncio.CancelledError):
        await thawing_status

    mock_thawer_control.assert_has_calls(
        [
            call(ThawerStates.ON, wait=ANY),
            call(ThawerStates.OFF, wait=ANY),
        ]
    )


async def test_calling_stop_on_thawer_stops_thawing_timer_and_turns_thawer_off(
    thawer: Thawer,
):
    thawer.thaw_for_time_s.stop = AsyncMock(spec=ThawingTimer)
    await thawer.stop()
    thawer.thaw_for_time_s.stop.assert_called_once()
    get_mock_put(thawer.control).assert_called_once_with(ThawerStates.OFF, wait=ANY)


@pytest.mark.skip(
    "Re-enable when https://github.com/bluesky/ophyd-async/issues/410 done"
)
async def test_thawing_timer_does_not_override_the_name_of_the_control_signal(
    thawer: Thawer,
):
    assert thawer.control.name == "thawer-control"
    assert thawer.thaw_for_time_s.name == "thawer-thaw_for_time_s"
