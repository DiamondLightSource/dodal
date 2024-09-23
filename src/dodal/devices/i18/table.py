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


class Table(StandardReadable):
    def __init__(self, motion_prefix: str, prefix: str = "", name: str = "") -> None:
        with self.add_children_as_readables():
            self.x = Motor(motion_prefix + "X")
            self.y = Motor(motion_prefix + "Y")
            self.z = Motor(motion_prefix + "Z")
            self.theta = Motor(motion_prefix + "THETA")

    @AsyncStatus.wrap
    async def set_xy(self, value: XYPosition):
        self.x.set(value.x)
        self.y.set(value.y)
