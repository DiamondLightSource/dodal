from dataclasses import dataclass

from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
)
from ophyd_async.epics.motor import Motor


@dataclass
class XYPosition:
    x: float
    y: float


class RasterStage(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x = Motor(prefix + "M1")
            self.y = Motor(prefix + "M2")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set_xy(self, value: XYPosition):
        self.x.set(value.x)
        self.y.set(value.y)
