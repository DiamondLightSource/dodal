from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
)
from ophyd_async.epics.motor import Motor
from pydantic import BaseModel


class TablePosition(BaseModel):
    x: float
    y: float
    z: float | None = None
    theta: float | None = None


class Table(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")
            self.y = Motor(prefix + "Y")
            self.z = Motor(prefix + "Z")
            self.theta = Motor(prefix + "THETA")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: TablePosition):
        self.x.set(value.x)
        self.y.set(value.y)
        if value.z:
            self.z.set(value.z)
        if value.theta:
            self.theta.set(value.theta)
