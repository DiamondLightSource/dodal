from ophyd_async.epics.motor import Motor

from dodal.devices.slits import Slits


class I10Slits(Slits):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x_ring_blade = Motor(prefix + "XRING")
            self.x_hall_blade = Motor(prefix + "XHALL")
            self.y_top_blade = Motor(prefix + "YPLUS")
            self.y_bot_blade = Motor(prefix + "YMINUS")
        super().__init__(
            prefix=prefix,
            x_gap="XSIZE",
            x_centre="XCENTRE",
            y_gap="YSIZE",
            y_centre="YCENTRE",
            name=name,
        )


class I10PrimarySlits(Slits):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x_aptr_1 = Motor(prefix + "APTR1:X")
            self.x_aptr_2 = Motor(prefix + "APTR2:X")
            self.y_aptr_1 = Motor(prefix + "APTR1:Y")
            self.y_aptr_1 = Motor(prefix + "APTR2:Y")
        super().__init__(
            prefix=prefix,
            x_gap="XSIZE",
            x_centre="XCENTRE",
            y_gap="YSIZE",
            y_centre="YCENTRE",
            name=name,
        )
