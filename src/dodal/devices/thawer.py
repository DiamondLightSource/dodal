from asyncio import Task, create_task, sleep

from bluesky.protocols import Movable, Stoppable
from ophyd_async.core import (
    AsyncStatus,
    Device,
    Reference,
    SignalRW,
    StandardReadable,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_rw


class ThawingException(Exception):
    pass


class ThawerStates(StrictEnum):
    OFF = "Off"
    ON = "On"


class ThawingTimer(Device, Stoppable, Movable[float]):
    def __init__(self, control_signal: SignalRW[ThawerStates]) -> None:
        self._control_signal_ref = Reference(control_signal)
        self._thawing_task: Task | None = None
        super().__init__("thaw_for_time_s")

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self._control_signal_ref().set(ThawerStates.ON)
        if self._thawing_task and not self._thawing_task.done():
            raise ThawingException("Thawing task already in progress")
        self._thawing_task = create_task(sleep(value))
        try:
            await self._thawing_task
        finally:
            await self._control_signal_ref().set(ThawerStates.OFF)

    @AsyncStatus.wrap
    async def stop(self, *args, **kwargs):
        if self._thawing_task:
            self._thawing_task.cancel()


class Thawer(StandardReadable, Stoppable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_rw(ThawerStates, prefix + ":CTRL")
        self.thaw_for_time_s = ThawingTimer(self.control)
        super().__init__(name)

    @AsyncStatus.wrap
    async def stop(self, *args, **kwargs):
        await self.thaw_for_time_s.stop()
        await self.control.set(ThawerStates.OFF)
