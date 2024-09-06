from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class DetectorMotion(StandardReadable):
    """Physical motion for detector travel"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.y = Motor(prefix + "Y")  # Vertical
        self.z = Motor(prefix + "Z")  # Beam

        super().__init__(name)
