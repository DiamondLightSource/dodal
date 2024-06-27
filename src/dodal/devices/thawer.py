from asyncio import Task, create_task, sleep
from enum import Enum

from bluesky.protocols import Stoppable
from ophyd_async.core import AsyncStatus, Device, SignalRW, StandardReadable
from ophyd_async.epics.signal import epics_signal_rw


class ThawingException(Exception):
    pass


class ThawerStates(str, Enum):
    OFF = "Off"
    ON = "On"


class ThawingTimer(Device):
    def __init__(self, control_signal: SignalRW[ThawerStates]) -> None:
        self._control_signal = control_signal
        self._thawing_task: Task | None = None
        super().__init__("thaw_for_time_s")

    @AsyncStatus.wrap
    async def set(self, time_to_thaw_for: float):
        await self._control_signal.set(ThawerStates.ON)
        if self._thawing_task and not self._thawing_task.done():
            raise ThawingException("Thawing task already in progress")
        self._thawing_task = create_task(sleep(time_to_thaw_for))
        try:
            await self._thawing_task
        finally:
            await self._control_signal.set(ThawerStates.OFF)

    async def stop(self):
        if self._thawing_task:
            self._thawing_task.cancel()


class Thawer(StandardReadable, Stoppable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_rw(ThawerStates, prefix + ":CTRL")
        self.thaw_for_time_s = ThawingTimer(self.control)
        super().__init__(name)

    async def stop(self):
        await self.thaw_for_time_s.stop()
        await self.control.set(ThawerStates.OFF)
