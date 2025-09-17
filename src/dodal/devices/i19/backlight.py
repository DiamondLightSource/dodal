from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.common.enums import InOutUpper


class BacklightPosition(StandardReadable, Movable[InOutUpper]):
    """Device moves backlight to the IN or OUT position since controls side manages switching the light on/off"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.position = epics_signal_rw(InOutUpper, f"{prefix}AD1:choiceButton")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: InOutUpper):
        await self.position.set(value, wait=True)
