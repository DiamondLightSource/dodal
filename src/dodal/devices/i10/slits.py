from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class I10Slit(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x_gap = Motor(prefix + "XSIZE")
            self.y_gap = Motor(prefix + "YSIZE")
            self.x_centre = Motor(prefix + "XCENTRE")
            self.y_centre = Motor(prefix + "YCENTRE")
            self.x_ring_blade = Motor(prefix + "XRING")
            self.x_hall_blade = Motor(prefix + "XHALL")
            self.y_top_blade = Motor(prefix + "YPLUS")
            self.y_bot_blade = Motor(prefix + "YMINUS")
        super().__init__(name=name)


class I10ExitSlit(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x_gap = Motor(prefix + "XSIZE")
            self.y_gap = Motor(prefix + "YSIZE")
        super().__init__(name=name)


class I10PrimarySlit(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x_gap = Motor(prefix + "XSIZE")
            self.y_gap = Motor(prefix + "YSIZE")
            self.x_centre = Motor(prefix + "XCENTRE")
            self.y_centre = Motor(prefix + "YCENTRE")
            self.x_aptr_1 = Motor(prefix + "APTR1:X")
            self.x_aptr_2 = Motor(prefix + "APTR2:X")
            self.y_aptr_1 = Motor(prefix + "APTR1:Y")
            self.y_aptr_1 = Motor(prefix + "APTR2:Y")
        super().__init__(name=name)
