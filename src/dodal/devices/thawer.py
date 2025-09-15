from asyncio import CancelledError, Task, create_task, sleep

from bluesky.protocols import Movable, Stoppable
from ophyd_async.core import (
    AsyncStatus,
    Device,
    OnOff,
    Reference,
    SignalRW,
    StandardReadable,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.log import LOGGER


class ThawingException(Exception):
    pass


class ThawingTimer(Device, Stoppable, Movable[float]):
    def __init__(self, control_signal: SignalRW[OnOff]) -> None:
        self._control_signal_ref = Reference(control_signal)
        self._thawing_task: Task | None = None
        super().__init__("thaw_for_time_s")

    @AsyncStatus.wrap
    async def set(self, value: float):
        if self._thawing_task:
            LOGGER.info("Thawing task already in progress, resetting timer")
            self._thawing_task.cancel()
        else:
            LOGGER.info("Thawing started")
            await self._control_signal_ref().set(OnOff.ON)
        self._thawing_task = create_task(sleep(value))
        try:
            await self._thawing_task
        except CancelledError:
            LOGGER.info("Timer task cancelled.")
            raise
        else:
            LOGGER.info("Thawing completed")
            await self._control_signal_ref().set(OnOff.OFF)

    @AsyncStatus.wrap
    async def stop(self, *args, **kwargs):
        if self._thawing_task:
            self._thawing_task.cancel()
            self._thawing_task = None
        LOGGER.info("Thawer stopped.")
        await self._control_signal_ref().set(OnOff.OFF)


class Thawer(StandardReadable, Stoppable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_rw(OnOff, prefix + ":CTRL")
        self.thaw_for_time_s = ThawingTimer(self.control)
        super().__init__(name)

    @AsyncStatus.wrap
    async def stop(self, *args, **kwargs):
        await self.thaw_for_time_s.stop()
        await self.control.set(OnOff.OFF)
