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
    """Device to move the beamstop.

    The positioner moves the x,y,z motors when a position is selected.
    The additional rot_y motor is independent of the positioner and can to be moved
    on its own as needed.

    WARNING. Before moving the rot_y motor away from 0, it is important to make sure
    that the backlight is in the "OUT" position to avoid a collision.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        self.roty = Motor(prefix + "ROTY")

        self.pos_select = epics_signal_rw(BSPositions, prefix + "MP:SELECT")

        super().__init__(name)
