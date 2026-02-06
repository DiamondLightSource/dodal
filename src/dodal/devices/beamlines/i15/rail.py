from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class Rail(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.pitch = Motor(prefix + "PITCH")
            self.y = Motor(prefix + "Y")
            self.y1 = Motor(prefix + "Y1")
            self.y2 = Motor(prefix + "Y2")

        super().__init__(name)
