from asyncio import Task, create_task, sleep
from enum import Enum

from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_rw
from ophyd_async.epics.signal import epics_signal_rw


class ThawingException(Exception):
    pass


class ThawerStates(str, Enum):
    OFF = "Off"
    ON = "On"


class Thawer(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_rw(ThawerStates, prefix + ":CTRL")
        self.thaw_time_s = soft_signal_rw(float, 10, name="thaw_time_s")
        self.thawing_task: Task | None = None
        super().__init__(name)

    @AsyncStatus.wrap
    async def kickoff(self):
        await self.control.set(ThawerStates.ON)
        if self.thawing_task and not self.thawing_task.done:
            raise ThawingException("Thawing task already in progress")
        self.thawing_task = create_task(sleep(await self.thaw_time_s.get_value()))

    @AsyncStatus.wrap
    async def complete(self):
        if not self.thawing_task:
            raise ThawingException("Kickoff called before complete")
        await self.thawing_task
