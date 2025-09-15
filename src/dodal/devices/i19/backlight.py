from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw


class InOutUpper(StrictEnum):
    IN = "IN"
    OUT = "OUT"


class BacklightPosition(StandardReadable, Movable[InOutUpper]):
    """Device moves backlight to the IN or OUT position since controls side manages switching the light on/off"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.position = epics_signal_rw(
            InOutUpper, prefix + "-EA-IOC-12:AD1:choiceButton"
        )
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: InOutUpper):
        await self.position.set(value, wait=True)
