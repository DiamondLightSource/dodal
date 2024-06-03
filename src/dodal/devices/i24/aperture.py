from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_rw


class ApPosition(str, Enum):
    IN = "In"
    OUT = "Out"
    ROBOT = "Robot"
    MANUAL = "Manual Mounting"


class AperturePositioner(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.pos_select = epics_signal_rw(ApPosition, prefix + "MP:SELECT")
        super().__init__(name)


class Aperture(StandardReadable):
    """Device to trigger the aperture motor move on I24.

    The aperture positioner has 4 possible positions: In, Out, Robot and Manual.

    When a position is selected, the x motor is moved.
    The position of the y motor is calibrated at start up and is not changed.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")

        self.pos = AperturePositioner(prefix, name)
        super().__init__(name)
