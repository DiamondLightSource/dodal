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


class XYZPositioner(StandardReadable):
    """

    Standard ophyd_async xyz motor stage, by combining 3 Motors,
    with added infix for extra flexibliy to allow different axes other than x,y,z.

    Parameters
    ----------
    prefix:
        EPICS PV (Common part up to and including :).
    name:
        name for the stage.
    infix:
        EPICS PV, default is the ("X", "Y", "Z").
    Notes
    -----
    Example usage::
        async with init_devices():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:")
    Or::
        with init_devices():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:", infix = ("A", "B", "C"))

    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        infix: tuple[str, str, str] = ("X", "Y", "Z"),
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + infix[0])
            self.y = Motor(prefix + infix[1])
            self.z = Motor(prefix + infix[2])
        super().__init__(name=name)


class SixAxisGonio(XYZPositioner):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        infix: tuple[str, str, str, str, str, str] = (
            "X",
            "Y",
            "Z",
            "KAPPA",
            "PHI",
            "OMEGA",
        ),
    ):
        with self.add_children_as_readables():
            self.kappa = Motor(prefix + infix[3])
            self.phi = Motor(prefix + infix[4])
            self.omega = Motor(prefix + infix[5])
        super().__init__(name=name, prefix=prefix, infix=infix[0:3])
