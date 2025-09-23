import asyncio
import contextlib

import pytest
from ophyd_async.core import (
    AsyncStatus,
    WatchableAsyncStatus,
    WatcherUpdate,
    observe_value,
    soft_signal_rw,
)

from dodal.common.watcher_utils import log_on_percentage_complete


class MockWatchable:
    def __init__(self):
        self.initial = 0
        self.final = 100
        self.signal = soft_signal_rw(int, 0)
        self.complete_event = asyncio.Event()
        self.done_status = AsyncStatus(self.complete_event.wait())

    @WatchableAsyncStatus.wrap
    async def get_watchable_status(self):
        """Asynchronously move the motor to a new position."""
        with contextlib.suppress(asyncio.CancelledError):
            async for current_position in observe_value(
                self.signal, done_status=self.done_status
            ):
                yield WatcherUpdate(
                    current=current_position,
                    initial=self.initial,
                    target=self.final,
                )


async def test_log_on_percentage_complete(caplog, RE):
    test_watchable = MockWatchable()
    status = test_watchable.get_watchable_status()
    interval = 20
    message_prefix = "Test status"
    log_on_percentage_complete(status, message_prefix, interval)
    assert "Fake motor move" not in caplog.messages
    try:
        # Test that messages appear at the correct intervals
        for position in range(interval, 110, interval):
            await test_watchable.signal.set(position)
            if position // interval // 2:
                assert f"Test status: {position}%" in caplog.messages[-1]
    finally:
        test_watchable.complete_event.set()
        assert sum(s.startswith(message_prefix) for s in caplog.messages) == 5


async def test_log_on_percentage_complete_value_error_on_bad_input():
    test_watchable = MockWatchable()
    status = test_watchable.get_watchable_status()
    with pytest.raises(
        ValueError,
        match="Percent interval on class _LogOnPercentageProgressWatcher must be a positive number, but received 0",
    ):
        log_on_percentage_complete(status, "", 0)


async def test_log_on_percentage_complete_for_already_updating_status():
    test_watchable = MockWatchable()
    status = test_watchable.get_watchable_status()

    async def update_signal():
        for i in range(10):
            await test_watchable.signal.set(i)

    async def do_log():
        log_on_percentage_complete(status, "")

    await asyncio.gather(update_signal(), do_log())
