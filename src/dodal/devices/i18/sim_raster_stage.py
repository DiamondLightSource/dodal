from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
)
from ophyd_async.epics.motor import Motor


class RasterStage(StandardReadable, Movable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.offset_in_mm = Motor(prefix + "M1")
            self.perp_in_mm = Motor(prefix + "M2")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.offset_in_mm.set(value)
