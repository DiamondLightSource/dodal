from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, wait_for_value
from ophyd_async.core import Device as OphydAsyncDevice
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class SetWhenEnabled(OphydAsyncDevice, Movable[int]):
    """A device that sets the proc field of a PV when it becomes enabled."""

    def __init__(self, prefix: str, name: str = ""):
        self.proc = epics_signal_rw(int, prefix + ".PROC")
        self.disp = epics_signal_r(int, prefix + ".DISP")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: int):
        await wait_for_value(self.disp, 0, None)
        await self.proc.set(value)
