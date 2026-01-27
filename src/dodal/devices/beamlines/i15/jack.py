from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class JackX(StandardReadable):
    """Focusing Mirror"""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.rotation = Motor(prefix + "Ry")
            self.transx = Motor(prefix + "X")
            self.y1 = Motor(prefix + "Y1")
            self.y2 = Motor(prefix + "Y2")
            self.y3 = Motor(prefix + "Y3")

        super().__init__(name)


class JackY(StandardReadable):
    """Focusing Mirror"""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.j1 = Motor(prefix + "J1")
            self.j2 = Motor(prefix + "J2")
            self.j3 = Motor(prefix + "J3")
            self.pitch = Motor(prefix + "PITCH")
            self.roll = Motor(prefix + "ROLL")
            self.y = Motor(prefix + "Y")

        super().__init__(name)
