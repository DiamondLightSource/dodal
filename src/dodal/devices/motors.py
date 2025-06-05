import re

from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


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


class MotorGroup(StandardReadable):
    """
    Generic group of motors, dynamically created from a name -> PV dictionary
    """

    def __init__(self, motor_name_to_pv: dict[str, str], name=""):
        with self.add_children_as_readables():
            for raw_motor_name, pv in motor_name_to_pv.items():
                motor_name = safe_identifier(raw_motor_name)
                setattr(self, motor_name, Motor(pv, motor_name))
        super().__init__(name=name)


def safe_identifier(name: str) -> str:
    # Replace leading non-word chars or digits with a single underscore
    name = re.sub(r"\W|^(?=\d)", "_", name)
    # Avoid name manging: replace two or more leading or trailing underscores with one
    name = re.sub(r"^_+|_+$", "_", name)
    return name
