from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_rw


class BSPositions(str, Enum):
    CHECKBEAM = "CheckBeam"
    DATACOLLECTION = "Data Collection"
    DATACOLLECTIONFAR = "Data Collection Far"
    TRAYMOUNT = "Tray Mount"
    ROTATABLE = "Rotatable"
    ROBOT = "Robot"


class Beamstop(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        self.roty = Motor(prefix + "ROTY")

        self.pos_select = epics_signal_rw(BSPositions, prefix + "MP:SELECT")

        super().__init__(name)
