import asyncio
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from ophyd_async.core import DeviceCollector, get_mock_put

from dodal.devices.thawer import Thawer, ThawerStates, ThawingException, ThawingTimer


@pytest.fixture
def thawer(RE):
    with DeviceCollector(mock=True):
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
    mock_thawer_control.assert_called_once_with(ThawerStates.ON, wait=ANY, timeout=ANY)
    mock_sleep.assert_called_once_with(10)
    mock_sleep.assert_awaited_once()
    mock_thawer_control.reset_mock()
    release_sleep.set()
    await asyncio.sleep(0.01)
    mock_thawer_control.assert_called_once_with(ThawerStates.OFF, wait=ANY, timeout=ANY)
    assert triggering_status.done


@patch("dodal.devices.thawer.sleep")
async def test_given_thawing_already_triggered_when_triggered_again_then_fails(
    mock_sleep: AsyncMock,
    thawer: Thawer,
):
    patch_sleep(mock_sleep)

    thawer.thaw_for_time_s.set(10)

    await asyncio.sleep(0.01)

    with pytest.raises(ThawingException):
        await thawer.thaw_for_time_s.set(10)


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
            call(ThawerStates.ON, wait=ANY, timeout=ANY),
            call(ThawerStates.OFF, wait=ANY, timeout=ANY),
        ]
    )


async def test_calling_stop_on_thawer_stops_thawing(
    thawer: Thawer,
):
    thawer.thaw_for_time_s = MagicMock(spec=ThawingTimer)
    await thawer.stop()
    thawer.thaw_for_time_s.stop.assert_called_once()
