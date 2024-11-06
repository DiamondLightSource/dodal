from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class VerticalGoniometer(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "PINX")
        self.z = Motor(prefix + "PINZ")
        self.yh = Motor(prefix + "PINYH")
        self.omega = Motor(prefix + "OMEGA")

        self.real_x = Motor(prefix + "PINXS")
        self.real_z = Motor(prefix + "PINZS")
        self.fast_y = Motor(prefix + "PINYS")

        super().__init__(name)
