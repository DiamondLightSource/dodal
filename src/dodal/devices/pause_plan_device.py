import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from typing import Any

from bluesky.protocols import Readable, Stageable
from ophyd_async.core import (
    AsyncStatus,
    Device,
    SignalR,
    observe_value,
)


class PausePlanDevice(Device, Stageable, Readable):
    def __init__(
        self,
        signals_to_condition: dict[SignalR[Any], Callable[[Any], bool]],
        callable_when_paused: Callable[[], Awaitable[None]] | None = None,
        callable_on_resume: Callable[[], Awaitable[None]] | None = None,
        seconds_to_wait_before_resume: float = 5,
        name: str = "",
    ):
        self._signals_to_condition = signals_to_condition
        self._callable_when_paused = callable_when_paused
        self._callable_on_resume = callable_on_resume
        self._seconds_to_wait_before_resume = seconds_to_wait_before_resume
        super().__init__(name)

    async def _pause(self):
        """Pause until all signal conditions are met, calling hooks as needed."""
        # Check if we actually need to pause
        values = await asyncio.gather(
            *(sig.get_value() for sig in self._signals_to_condition)
        )
        all_met = all(
            pred(value)
            for value, (_, pred) in zip(
                values, self._signals_to_condition.items(), strict=True
            )
        )
        if all_met:
            return  # no need to pause

        # Call pause hook
        if self._callable_when_paused:
            await self._callable_when_paused()

        latest = {}
        event = asyncio.Event()

        async def watch(signal, predicate):
            async for value in observe_value(signal):
                latest[signal] = predicate(value)
                if len(latest) == len(self._signals_to_condition) and all(
                    latest.values()
                ):
                    event.set()
                    return

        tasks = [
            asyncio.create_task(watch(sig, pred))
            for sig, pred in self._signals_to_condition.items()
        ]

        await event.wait()

        # Cancel watchers
        for task in tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        await asyncio.sleep(self._seconds_to_wait_before_resume)
        # Call resume hook
        if self._callable_on_resume:
            await self._callable_on_resume()

    @AsyncStatus.wrap
    async def stage(self):
        await self._pause()

    @AsyncStatus.wrap
    async def unstage(self):
        pass

    async def read(self):
        await self._pause()
        return {}

    async def describe(self):
        return {}
