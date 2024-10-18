from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
)
from ophyd_async.epics.motor import Motor
from pydantic import BaseModel


class Four_D_Position(BaseModel):
    x: float
    y: float
    z: float
    theta: float


class Table(StandardReadable):
    def __init__(self, prefix: str = "", name: str = "") -> None:
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")
            self.y = Motor(prefix + "Y")
            self.z = Motor(prefix + "Z")
            self.theta = Motor(prefix + "THETA")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: Four_D_Position):
        self.x.set(value.x)
        self.y.set(value.y)
