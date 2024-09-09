from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class Scatterguard(StandardReadable):
    """The scatterguard device."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        super().__init__(name)
