from ophyd_async.core import StandardReadable

from dodal.devices.util.motor_utils import ExtendedMotor


class Scatterguard(StandardReadable):
    """The scatterguard device."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = ExtendedMotor(prefix + "X")
        self.y = ExtendedMotor(prefix + "Y")
        super().__init__(name)
