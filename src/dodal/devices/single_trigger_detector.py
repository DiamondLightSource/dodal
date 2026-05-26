import asyncio
from collections.abc import Sequence

from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, SignalR, StandardReadable
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.adcore import ADBaseIO, ADImageMode, NDPluginBaseIO


class SingleTriggerDetector(StandardReadable, Triggerable):
    """A minimal triggerable detector that takes a single image and reads plugin
    statistics. Does not write files. Replaces the removed ophyd-async class of
    the same name.
    """

    def __init__(
        self,
        drv: ADBaseIO,
        read_uncached: Sequence[SignalR] = (),
        name: str = "",
        plugins: dict[str, NDPluginBaseIO] | None = None,
    ) -> None:
        self.drv = drv
        if plugins is not None:
            for k, v in plugins.items():
                setattr(self, k, v)
        self.add_readables(
            [self.drv.array_counter, *read_uncached],
            Format.HINTED_UNCACHED_SIGNAL,
        )
        self.add_readables([self.drv.acquire_time], Format.CONFIG_SIGNAL)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await asyncio.gather(
            self.drv.image_mode.set(ADImageMode.SINGLE),
            self.drv.wait_for_plugins.set(True),
        )
        await super().stage()

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await self.drv.acquire.set(True)
