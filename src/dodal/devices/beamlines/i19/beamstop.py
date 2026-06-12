from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw, epics_signal_x

from dodal.devices.motors import XYZStage


class HomeGroup(StrictEnum):
    NONE = "none"
    ALL = "ALL"
    X = "X"
    Y = "Y"
    Z = "Z"


class HomingControl(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.homing_group = epics_signal_rw(HomeGroup, f"{prefix}:HMGRP")
        self.home = epics_signal_x(f"{prefix}:HOME")
        super().__init__(name)


class BeamStop(XYZStage):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.homing = HomingControl(f"{prefix}HM", name)

        super().__init__(prefix, name)
