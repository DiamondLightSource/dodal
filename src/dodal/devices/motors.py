import asyncio
import math

from ophyd_async.core import StandardReadable, derived_signal_rw
from ophyd_async.epics.motor import Motor


def create_axis_perp_to_rotation(motor_theta: Motor, motor_i: Motor, motor_j: Motor):
    """Given a signal that controls a motor in a rotation axis and two other
    signals controlling motors on a pair of orthogonal axes, these axes being in the
    rotating frame of reference created by the first axis, create a derived signal
    that is a projection of the two axes in the non-rotating frame of reference.

    The projection is onto the axis defined by i when the rotation angle is 0 and
    defined by j when the angle is minus 90.

    The usual use case for this is translating from sample space to lab space. For
    example, if you have a sample that is mounted on a goniometer to the right hand side
    of an OAV view this can provide an axis that will move the sample up/down in that
    view regardless of the omega orientation of the sample.

    Args:
        motor_theta (Motor): this is the rotation axis of the sample.
        motor_i (Motor): this is the axis that, when the sample is at 0 deg rotation,
                         a move here is entirely parallel with the derived axis.
        motor_j (Motor): this is the axis that, when the sample is at -90 deg rotation,
                         a move here is entirely parallel with the derived axis.
    """

    def _get(j_val: float, i_val: float, rot_value: float) -> float:
        i_component = i_val * math.cos(math.radians(rot_value))
        j_component = j_val * math.sin(math.radians(rot_value))
        return i_component + j_component

    async def _set(vertical_value: float) -> None:
        rot_value = await motor_theta.user_readback.get_value()
        i_component = vertical_value * math.cos(math.radians(rot_value))
        j_component = vertical_value * math.sin(math.radians(rot_value))
        await asyncio.gather(
            motor_i.set(i_component),
            motor_j.set(j_component),
            motor_theta.set(rot_value),
        )

    return derived_signal_rw(
        _get,
        _set,
        i_val=motor_i,
        j_val=motor_j,
        rot_value=motor_theta,
    )


class XYZPositioner(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        infix: tuple[str, str, str] = ("X", "Y", "Z"),
    ):
        """Standard ophyd_async xyz motor stage, by combining 3 Motors,
        with added infix for extra flexibility to allow different axes other than x,y,z.

        Args:
            prefix: EPICS PV (Common part up to and including :).
            name: name for the device.
            infix: EPICS PV suffix, default is the ("X", "Y", "Z").

        """
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
        """Six-axis goniometer with a standard xyz stage and three axes of rotation:
        kappa, phi and omega.

        Args:
            prefix: EPICS PV (Common part up to and including :).
            name: name for the device.
            infix: EPICS PV suffix, default is the ("X", "Y", "Z", "KAPPA", "PHI", "OMEGA").
        """
        with self.add_children_as_readables():
            self.kappa = Motor(prefix + infix[3])
            self.phi = Motor(prefix + infix[4])
            self.omega = Motor(prefix + infix[5])

        super().__init__(name=name, prefix=prefix, infix=infix[0:3])

        self.vertical_in_lab_space = create_axis_perp_to_rotation(
            self.omega, self.y, self.z
        )
