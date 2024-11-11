from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw
from ophyd_async.epics.motor import Motor


class BeamstopPositions(StrictEnum):
    CHECK_BEAM = "CheckBeam"
    DATA_COLLECTION = "Data Collection"
    DATA_COLLECTION_FAR = "Data Collection Far"
    TRAY_MOUNT = "Tray Mount"
    ROTATABLE = "Rotatable"
    ROBOT = "Robot"


class Beamstop(StandardReadable):
    """Device to move the beamstop.

    The positioner moves the x,y,z motors when a position is selected.
    The additional y_rotation motor is independent of the positioner and can to be moved
    on its own as needed.

    WARNING. Before moving the y_rotation motor away from 0, it is important to make sure
    that the backlight is in the "OUT" position to avoid a collision.
    See also https://github.com/DiamondLightSource/dodal/issues/646.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")

        self.y_rotation = Motor(prefix + "ROTY")

        self.pos_select = epics_signal_rw(BeamstopPositions, prefix + "MP:SELECT")

        super().__init__(name)
