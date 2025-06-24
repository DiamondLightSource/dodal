from abc import ABC

from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor

_X, _Y, _Z = "X", "Y", "Z"


class Stage(StandardReadable, ABC):
    """
    For these devices, the following co-ordinates are typical but not enforced:
    - z is horizontal & parallel to the direction of beam travel
    - y is vertical and antiparallel to the force of gravity
    - x is the cross product of y🞬z

    Parameters
    ----------
    prefix:
        Common part of the EPICS PV for all motors, including ":".
    name:
        Name of the stage, each child motor will be named "{name}-{field_name}"
    *_infix:
        Infix between the common prefix and the EPICS motor record fields for the field.
    """

    ...


class XThetaStage(Stage):
    def __init__(
        self, prefix: str, name: str = "", x_infix: str = _X, theta_infix: str = "A"
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + x_infix)
            self.theta = Motor(prefix + theta_infix)
        super().__init__(name=name)


class XYStage(Stage):
    def __init__(
        self, prefix: str, name: str = "", x_infix: str = _X, y_infix: str = _Y
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + x_infix)
            self.y = Motor(prefix + y_infix)
        super().__init__(name=name)


class XYZStage(XYStage):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
    ):
        with self.add_children_as_readables():
            self.z = Motor(prefix + z_infix)
        super().__init__(prefix, name, x_infix, y_infix)


class XYZThetaStage(XYZStage):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        theta_infix: str = _Z,
    ) -> None:
        with self.add_children_as_readables():
            self.theta = Motor(prefix + theta_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class XYPitchStage(XYStage):
    def __init__(
        self,
        prefix: str,
        x_infix: str = _X,
        y_infix: str = _Y,
        pitch_infix: str = "PITCH",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.pitch = Motor(prefix + pitch_infix)
        super().__init__(prefix, name, x_infix, y_infix)


class SixAxisGonio(XYZStage):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        kappa_infix: str = "KAPPA",
        phi_infix: str = "PHI",
        omega_infix: str = "OMEGA",
    ):
        with self.add_children_as_readables():
            self.kappa = Motor(prefix + kappa_infix)
            self.phi = Motor(prefix + phi_infix)
            self.omega = Motor(prefix + omega_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class YZStage(Stage):
    def __init__(
        self, prefix: str, name: str = "", y_infix: str = _Y, z_infix: str = _Z
    ) -> None:
        with self.add_children_as_readables():
            self.y = Motor(prefix + y_infix)
            self.z = Motor(prefix + z_infix)
        super().__init__(name)
