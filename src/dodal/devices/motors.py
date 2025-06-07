import asyncio
import math

from ophyd_async.core import StandardReadable, derived_signal_rw
from ophyd_async.epics.motor import Motor


def create_axis_perp_to_rotation(
    parallel_to_0: Motor, parallel_to_minus_90: Motor, rotation: Motor
):
    """Create a new derived signal that moves perpendicular to a rotation axis.

    The usual use case for this is translating from sample space to lab space. For
    example, if you have a sample that is mounted on a goniometer to the right hand side
    of an OAV view this can provide an axis that will move the sample up/down in that
    view regardless of the omega orientation of the sample.

    Args:
        parallel_to_0 (Motor): this is the axis that, when the sample is at 0 deg rotation,
                               a move here is entirely parallel with the derived axis.
        parallel_to_minus_90 (Motor): this is the axis that, when the sample is at 90 deg
                                      rotation, a move here is entirely parallel with the
                                      derived axis.
        rotation (Motor): this is the rotation axis of the sample.
    """
    # By convention use y/z internally as that is what is used on most beamlines but the
    # function is actually indifferent to this
    y_mot = parallel_to_0
    z_mot = parallel_to_minus_90

    def _get(z_val: float, y_val: float, rot_value: float) -> float:
        y_component = y_val * math.cos(math.radians(rot_value))
        z_component = z_val * math.sin(math.radians(rot_value))
        return z_component + y_component

    async def _set(vertical_value: float) -> None:
        rot_value = await rotation.user_readback.get_value()
        y_component = vertical_value * math.cos(math.radians(rot_value))
        z_component = vertical_value * math.sin(math.radians(rot_value))
        await asyncio.gather(
            y_mot.set(y_component),
            z_mot.set(z_component),
            rotation.set(rot_value),
        )

    return derived_signal_rw(
        _get,
        _set,
        y_val=y_mot,
        z_val=z_mot,
        rot_value=rotation,
    )


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
    """

    Six-axis goniometer with a standard xyz stage and three axes of rotation: kappa, phi
    and omega.

        Parameters
    ----------
    prefix:
        EPICS PV (Common part up to and including :).
    name:
        name for the stage.
    infix:
        EPICS PV, default is the ("X", "Y", "Z", "KAPPA", "PHI", "OMEGA").
    Notes
    -----
    Example usage::
        async with init_devices():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:")
    Or::
        with init_devices():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:", infix = ("A", "B", "C", \
            "KAPPA", "PHI", "OMEGA"))

    """

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

        self.vertical_in_lab_space = create_axis_perp_to_rotation(
            self.y, self.z, self.omega
        )
