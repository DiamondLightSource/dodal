from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw
from ophyd_async.epics.motor import Motor


class AperturePositions(StrictEnum):
    IN = "In"
    OUT = "Out"
    ROBOT = "Robot"
    MANUAL = "Manual Mounting"


class Aperture(StandardReadable):
    """Device to trigger the aperture motor move on I24.

    The aperture positioner has 4 possible positions: In, Out, Robot and Manual.

    When a position is selected, the x motor is moved.
    The position of the y motor is calibrated at start up and is not changed.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")

        self.position = epics_signal_rw(AperturePositions, prefix + "MP:SELECT")
        super().__init__(name)
