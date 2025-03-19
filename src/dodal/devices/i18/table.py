from ophyd_async.core import (
    StandardReadable,
)
from ophyd_async.epics.motor import Motor


class Table(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")
            self.y = Motor(prefix + "Y")
            self.z = Motor(prefix + "Z")
            self.theta = Motor(prefix + "THETA")
        super().__init__(name=name)
