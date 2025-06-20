from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class XThetaStage(StandardReadable):
    """

    ophyd_async x theta motor stage, combining 2 Motors: a horizontal stage and a
    rotational stage mutually perpendicular to each other and the beam.

    Parameters
    ----------
    prefix:
        Common part of the EPICS PV for all motors, including ":".
    name:
        Name of the stage, each child motor will be named "{name}-{field_name}"
    *_infix:
        Infix between the common prefix and the EPICS motor record fields for the field.

    """

    def __init__(
        self, prefix: str, name: str = "", x_infix: str = "X", theta_infix: str = "A"
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + x_infix)
            self.theta = Motor(prefix + theta_infix)
        super().__init__(name=name)


class XYStage(StandardReadable):
    """

    ophyd_async x y motor stage, combining 2 Motors, mutually perpendicular to the beam.

    Parameters
    ----------
    prefix:
        Common part of the EPICS PV for all motors, including ":".
    name:
        Name of the stage, each child motor will be named "{name}-{field_name}"
    *_infix:
        Infix between the common prefix and the EPICS motor record fields for the field.

    """

    def __init__(
        self, prefix: str, name: str = "", x_infix: str = "X", y_infix: str = "Y"
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + x_infix)
            self.y = Motor(prefix + y_infix)
        super().__init__(name=name)


class XYZStage(XYStage):
    """

    ophyd_async x y z motor stage, combining 3  mutually perpendicular Motors.

    Parameters
    ----------
    prefix:
        Common part of the EPICS PV for all motors, including ":".
    name:
        Name of the stage, each child motor will be named "{name}-{field_name}"
    *_infix:
        Infix between the common prefix and the EPICS motor record fields for the field.

    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = "X",
        y_infix: str = "Y",
        z_infix: str = "Z",
    ):
        with self.add_children_as_readables():
            self.z = Motor(prefix + z_infix)
        super().__init__(prefix, name, x_infix, y_infix)


class XYZThetaStage(XYZStage):
    """

    ophyd_async x y z theta motor stage, combining 3  mutually perpendicular Motors and
    a rotational stage in theta.

    Parameters
    ----------
    prefix:
        Common part of the EPICS PV for all motors, including ":".
    name:
        Name of the stage, each child motor will be named "{name}-{field_name}"
    *_infix:
        Infix between the common prefix and the EPICS motor record fields for the field.

    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = "X",
        y_infix: str = "Y",
        z_infix: str = "Z",
        theta_infix: str = "Z",
    ) -> None:
        with self.add_children_as_readables():
            self.theta = Motor(prefix + theta_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class SixAxisGonio(XYZStage):
    """

    ophyd_async x y z kappa phi omega motor stage, combining 3  mutually perpendicular
    Motors and 3 mutually perpendicular rotational stages.

    Parameters
    ----------
    prefix:
        Common part of the EPICS PV for all motors, including ":".
    name:
        Name of the stage, each child motor will be named "{name}-{field_name}"
    *_infix:
        Infix between the common prefix and the EPICS motor record fields for the field.

    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = "X",
        y_infix: str = "Y",
        z_infix: str = "Z",
        kappa_infix: str = "KAPPA",
        phi_infix: str = "PHI",
        omega_infix: str = "OMEGA",
    ):
        with self.add_children_as_readables():
            self.kappa = Motor(prefix + kappa_infix)
            self.phi = Motor(prefix + phi_infix)
            self.omega = Motor(prefix + omega_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class YZStage(StandardReadable):
    """Physical motion for detector travel

    ophyd_async y z motor stage, combining 2 Motors: a horizontal stage parallel to the
    beam and a vertical stage perpendicular to it.

    Parameters
    ----------
    prefix:
        Common part of the EPICS PV for all motors, including ":".
    name:
        Name of the stage, each child motor will be named "{name}-{field_name}"
    *_infix:
        Infix between the common prefix and the EPICS motor record fields for the field.

    """

    def __init__(
        self, prefix: str, name: str = "", y_infix: str = "Y", z_infix: str = "Z"
    ) -> None:
        self.y = Motor(prefix + y_infix)  # Vertical
        self.z = Motor(prefix + z_infix)  # Beam

        super().__init__(name)
