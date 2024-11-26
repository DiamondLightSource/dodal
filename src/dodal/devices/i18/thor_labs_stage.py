from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
)
from ophyd_async.epics.motor import Motor
from pydantic import BaseModel


class XYPosition(BaseModel):
    x: float
    y: float


class ThorLabsStage(StandardReadable):
    def __init__(self, prefix: str = "", name: str = "") -> None:
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")
            self.y = Motor(prefix + "Y")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: XYPosition):
        self.x.set(value.x)
        self.y.set(value.y)
