import asyncio
import math
from abc import ABC

from ophyd_async.core import SignalRW, StandardReadable, derived_signal_rw
from ophyd_async.epics.motor import Motor

_X, _Y, _Z = "X", "Y", "Z"

_OMEGA = "OMEGA"
_POLAR = "POLAR"
_AZIMUTH = "AZIMUTH"
_TILT = "TILT"


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
    """
    Two-axis stage with an x and a theta motor.
    """

    def __init__(
        self, prefix: str, name: str = "", x_infix: str = _X, theta_infix: str = "A"
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + x_infix)
            self.theta = Motor(prefix + theta_infix)
        super().__init__(name=name)


class XYStage(Stage):
    """
    A standard two-axis stage with an x and a y motor.
    """

    def __init__(
        self, prefix: str, name: str = "", x_infix: str = _X, y_infix: str = _Y
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + x_infix)
            self.y = Motor(prefix + y_infix)
        super().__init__(name=name)


class XYZStage(XYStage):
    """
    A standard three-axis stage with an x, a y, and a z motor.
    """

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
    """
    Four-axis stage with a standard xyz stage and one axis of rotation: theta.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        theta_infix: str = "THETA",
    ) -> None:
        with self.add_children_as_readables():
            self.theta = Motor(prefix + theta_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class XYZOmegaStage(XYZStage):
    """
    Four-axis stage with a standard xyz stage and one axis of rotation: omega.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        omega_infix: str = _OMEGA,
    ) -> None:
        with self.add_children_as_readables():
            self.omega = Motor(prefix + omega_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class XYZPolarStage(XYZStage):
    """Four-axis stage with a standard xyz stage and one axis of rotation: polar."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        polar_infix: str = _POLAR,
    ) -> None:
        with self.add_children_as_readables():
            self.polar = Motor(prefix + polar_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class XYZPolarAzimuthStage(XYZPolarStage):
    """
    Five-axis stage with a standard xyz stage and two axis of rotation: polar and azimuth.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        polar_infix: str = _POLAR,
        azimuth_infix: str = _AZIMUTH,
    ):
        with self.add_children_as_readables():
            self.azimuth = Motor(prefix + azimuth_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix, polar_infix)


class XYZPolarAzimuthTiltStage(XYZPolarAzimuthStage):
    """
    Six-axis stage with a standard xyz stage and three axis of rotation: polar, azimuth
    and tilt.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        polar_infix: str = _POLAR,
        azimuth_infix: str = _AZIMUTH,
        tilt_infix: str = _TILT,
    ):
        with self.add_children_as_readables():
            self.tilt = Motor(prefix + tilt_infix)
        super().__init__(
            prefix, name, x_infix, y_infix, z_infix, polar_infix, azimuth_infix
        )


class XYPhiStage(XYStage):
    """
    Three-axis stage with a standard xy stage and one axis of rotation: phi.
    """

    def __init__(
        self,
        prefix: str,
        x_infix: str = _X,
        y_infix: str = _Y,
        phi_infix: str = "PHI",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.phi = Motor(prefix + phi_infix)
        super().__init__(prefix, name, x_infix, y_infix)


class XYPitchStage(XYStage):
    """
    Three-axis stage with a standard xy stage and one axis of rotation: pitch.
    """

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


class XYRollStage(XYStage):
    """
    Three-axis stage with a standard xy stage and one axis of rotation: roll.
    """

    def __init__(
        self,
        prefix: str,
        x_infix: str = _X,
        y_infix: str = _Y,
        roll_infix: str = "ROLL",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.roll = Motor(prefix + roll_infix)
        super().__init__(prefix, name, x_infix, y_infix)


class XYZPitchYawStage(XYZStage):
    """
    Five-axis stage with a standard xyz stage and two axes of rotation: pitch and yaw.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        pitch_infix="PITCH",
        yaw_infix="YAW",
    ):
        with self.add_children_as_readables():
            self.pitch = Motor(prefix + pitch_infix)
            self.yaw = Motor(prefix + yaw_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class XYZPitchYawRollStage(XYZStage):
    """
    Five-axis stage with a standard xyz stage and three axes of rotation: pitch, yaw,
    and roll.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        pitch_infix: str = "PITCH",
        yaw_infix: str = "YAW",
        roll_infix: str = "ROLL",
    ):
        with self.add_children_as_readables():
            self.pitch = Motor(prefix + pitch_infix)
            self.yaw = Motor(prefix + yaw_infix)
            self.roll = Motor(prefix + roll_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class SixAxisGonio(XYZOmegaStage):
    """
    Six-axis goniometer with a standard xyz stage and three axes of rotation:
    kappa, phi and omega.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        kappa_infix: str = "KAPPA",
        phi_infix: str = "PHI",
        omega_infix: str = _OMEGA,
    ):
        with self.add_children_as_readables():
            self.kappa = Motor(prefix + kappa_infix)
            self.phi = Motor(prefix + phi_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix, omega_infix)

        self.vertical_in_lab_space = create_axis_perp_to_rotation(
            self.omega, self.y, self.z
        )


class SixAxisGonioKappaPhi(XYZStage):
    """
    Six-axis goniometer with a standard xyz stage and two axes of rotation:
    kappa and phi.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        kappa_infix: str = "KAPPA",
        phi_infix: str = "PHI",
    ):
        with self.add_children_as_readables():
            self.kappa = Motor(prefix + kappa_infix)
            self.phi = Motor(prefix + phi_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class YZStage(Stage):
    """
    Two-axis stage with an x and a z motor.
    """

    def __init__(
        self, prefix: str, name: str = "", y_infix: str = _Y, z_infix: str = _Z
    ) -> None:
        with self.add_children_as_readables():
            self.y = Motor(prefix + y_infix)
            self.z = Motor(prefix + z_infix)
        super().__init__(name)


def create_axis_perp_to_rotation(
    motor_theta: Motor, motor_i: Motor, motor_j: Motor
) -> SignalRW[float]:
    """Given a signal that controls a motor in a rotation axis and two other
    signals controlling motors on a pair of orthogonal axes, these axes being in the
    rotating frame of reference created by the first axis, create a derived signal
    that is a projection of the two axes in the non-rotating frame of reference.

    The projection is onto the axis defined by i when the rotation angle is 0 and
    defined by j when the angle is at 90.

    The usual use case for this is translating from sample space to lab space. For
    example, if you have a sample that is mounted on a goniometer to the right hand side
    of an OAV view this can provide an axis that will move the sample up/down in that
    view regardless of the omega orientation of the sample.

    Args:
        motor_theta (Motor): this is the rotation axis of the sample.
        motor_i (Motor): this is the axis that, when the sample is at 0 deg rotation,
                         a move here is entirely parallel with the derived axis.
        motor_j (Motor): this is the axis that, when the sample is at 90 deg rotation,
                         a move here is entirely parallel with the derived axis.
    """

    def _get(j_val: float, i_val: float, rot_deg_value: float) -> float:
        i_component = i_val * math.cos(math.radians(rot_deg_value))
        j_component = j_val * math.sin(math.radians(rot_deg_value))
        return i_component + j_component

    async def _set(vertical_value: float) -> None:
        rot_deg_value = await motor_theta.user_readback.get_value()
        i_component = vertical_value * math.cos(math.radians(rot_deg_value))
        j_component = vertical_value * math.sin(math.radians(rot_deg_value))
        await asyncio.gather(
            motor_i.set(i_component),
            motor_j.set(j_component),
            motor_theta.set(rot_deg_value),
        )

    return derived_signal_rw(
        _get,
        _set,
        i_val=motor_i,
        j_val=motor_j,
        rot_deg_value=motor_theta,
    )
