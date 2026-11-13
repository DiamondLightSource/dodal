import asyncio

from bluesky.protocols import Movable, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_rw,
)


class WaitTime(StandardReadable, Movable[float], Triggerable):
    """Device that waits for a settable time when triggered."""

    def __init__(self, initial_value=1, name: str = "") -> None:
        super().__init__(name)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.time_to_wait = soft_signal_rw(float, initial_value)

    @AsyncStatus.wrap
    async def set(self, time: float):
        await self.time_to_wait.set(time)
        await asyncio.sleep(time)

    @AsyncStatus.wrap
    async def trigger(self):
        time = await self.time_to_wait.get_value()
        await asyncio.sleep(time)
