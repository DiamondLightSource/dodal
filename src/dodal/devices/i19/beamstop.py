from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw, epics_signal_x
from ophyd_async.epics.motor import Motor


class HomeGroup(StrictEnum):
    NONE = "none"
    ALL = "All"
    X = "X"
    Y = "Y"
    Z = "Z"


class HomingControl(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.homing_group = epics_signal_rw(HomeGroup, f"{prefix}:HMGRP")
        self.home = epics_signal_x(f"{prefix}:HOME")
        super().__init__(name)


class BeamStop(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.x = Motor(f"{prefix}X")
            self.y = Motor(f"{prefix}Y")
            self.z = Motor(f"{prefix}Z")

        self.homing = HomingControl(f"{prefix}HM", name)

        super().__init__(name)
