from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class Goniometer(StandardReadable):
    """Goniometer and the stages it sits on"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")
        self.sampy = Motor(prefix + "SAMPY")
        self.sampz = Motor(prefix + "SAMPZ")
        self.omega = Motor(prefix + "OMEGA")
        super().__init__(name)
