from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, InOut, StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw


class BacklightPosition(StandardReadable, Movable[InOut]):
    """Device moves backlight to the IN or OUT position since controls side manages switching the light on/off"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.position = epics_signal_rw(InOut, prefix + "-EA-IOC-12:AD1:choiceButton")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: InOut):
        await self.position.set(value, wait=True)
