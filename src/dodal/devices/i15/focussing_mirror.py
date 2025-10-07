from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class FocusingMirrorBase(StandardReadable):
    """Focusing Mirror with curve, ellip & pitch"""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.curve = Motor(prefix + "CURVE")
            self.ellipticity = Motor(prefix + "ELLIP")
            self.pitch = Motor(prefix + "PITCH")

        super().__init__(name)


class FocusingMirrorHorizontal(FocusingMirrorBase):
    """Focusing Mirror with curve, ellip, pitch & X"""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")

        super().__init__(prefix, name)


class FocusingMirrorVertical(FocusingMirrorBase):
    """Focusing Mirror with curve, ellip, pitch & Y"""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.y = Motor(prefix + "Y")

        super().__init__(prefix, name)


class FocusingMirror(FocusingMirrorBase):
    """Focusing Mirror with curve, ellip, pitch, yaw, X & Y"""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.yaw = Motor(prefix + "YAW")
            self.x = Motor(prefix + "X")
            self.y = Motor(prefix + "Y")

        super().__init__(prefix, name)


class FocusingMirrorWithRoll(FocusingMirror):
    """Focusing Mirror with curve, ellip, pitch, roll, yaw, X & Y"""

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.roll = Motor(prefix + "ROLL")
        super().__init__(prefix, name)
