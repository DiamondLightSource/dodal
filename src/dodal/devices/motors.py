import asyncio
import math
from abc import ABC
from math import radians

from bluesky.protocols import Movable
from bluesky.utils import maybe_await
from ophyd_async.core import (
    SignalR,
    SignalRW,
    StandardReadable,
    derived_signal_rw,
)
from ophyd_async.epics.motor import Motor

from dodal.common.maths import rotate_clockwise, rotate_counter_clockwise

_X, _Y, _Z = "X", "Y", "Z"

_OMEGA = "OMEGA"
_POLAR = "POLAR"
_AZIMUTH = "AZIMUTH"
_TILT = "TILT"


class Stage(StandardReadable, ABC):
    """For these devices, the following co-ordinates are typical but not enforced:
    - z is horizontal & parallel to the direction of beam travel
    - y is vertical and antiparallel to the force of gravity
    - x is the cross product of y🞬z

    Attributes:
        prefix (str): Common part of the EPICS PV for all motors, including ":".
        name (str, optional): Name of the stage, each child motor will be named
            "{name}-{field_name}".
        *_infix: Infix between the common prefix and the EPICS motor record fields for
            the field.
    """  # noqa D415

    ...


class XThetaStage(Stage):
    """Two-axis stage with an x and a theta motor."""

    def __init__(
        self, prefix: str, name: str = "", x_infix: str = _X, theta_infix: str = "A"
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + x_infix)
            self.theta = Motor(prefix + theta_infix)
        super().__init__(name=name)


class XYStage(Stage):
    """A standard two-axis stage with an x and a y motor."""

    def __init__(
        self, prefix: str, name: str = "", x_infix: str = _X, y_infix: str = _Y
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + x_infix)
            self.y = Motor(prefix + y_infix)
        super().__init__(name=name)


class XYZStage(XYStage):
    """A standard three-axis stage with an x, a y, and a z motor."""

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
    """Four-axis stage with a standard xyz stage and one axis of rotation: theta."""

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
    """Four-axis stage with a standard xyz stage and one axis of rotation: omega."""

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


class XYZAzimuthStage(XYZStage):
    """Four-axis stage with a standard xyz stage and one axis of rotation: azimuth."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        azimuth_infix: str = _AZIMUTH,
    ) -> None:
        with self.add_children_as_readables():
            self.azimuth = Motor(prefix + azimuth_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix)


class XYZAzimuthPolarStage(XYZAzimuthStage):
    """Four-axis stage with a standard xyz stage and two axis of rotation: azimuth
    and polar.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        azimuth_infix: str = _AZIMUTH,
        polar_infix: str = _POLAR,
    ) -> None:
        with self.add_children_as_readables():
            self.polar = Motor(prefix + polar_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix, azimuth_infix)


class XYZAzimuthTiltStage(XYZAzimuthStage):
    """Five-axis stage with a standard xyz stage and two axis of rotation: azimuth and
    tilt.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        azimuth_infix: str = _AZIMUTH,
        tilt_infix: str = _TILT,
    ):
        with self.add_children_as_readables():
            self.tilt = Motor(prefix + tilt_infix)
        super().__init__(prefix, name, x_infix, y_infix, z_infix, azimuth_infix)


class XYZAzimuthTiltPolarStage(XYZAzimuthTiltStage):
    """Six-axis stage with a standard xyz stage and three axis of rotation: azimuth,
    tilt and polar.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        azimuth_infix: str = _AZIMUTH,
        tilt_infix: str = _TILT,
        polar_infix: str = _POLAR,
    ):
        with self.add_children_as_readables():
            self.polar = Motor(prefix + polar_infix)
        super().__init__(
            prefix, name, x_infix, y_infix, z_infix, azimuth_infix, tilt_infix
        )


class XYPhiStage(XYStage):
    """Three-axis stage with a standard xy stage and one axis of rotation: phi."""

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
    """Three-axis stage with a standard xy stage and one axis of rotation: pitch."""

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
    """Three-axis stage with a standard xy stage and one axis of rotation: roll."""

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
    """Five-axis stage with a standard xyz stage and two axes of rotation: pitch and
    yaw.
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
    """Five-axis stage with a standard xyz stage and three axes of rotation: pitch, yaw,
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
    """Six-axis goniometer with a standard xyz stage and three axes of rotation:
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
    """Six-axis goniometer with a standard xyz stage and two axes of rotation:
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
    """Two-axis stage with an x and a z motor."""

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
        x, y = rotate_clockwise(math.radians(rot_deg_value), i_val, j_val)
        return x

    async def _set(vertical_value: float) -> None:
        rot_deg_value = await motor_theta.user_readback.get_value()
        theta = math.radians(rot_deg_value)
        i_component, j_component = rotate_counter_clockwise(theta, vertical_value, 0.0)
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


async def _get_angle_deg(angle_deg: SignalR[float] | float) -> float:
    if isinstance(angle_deg, SignalR):
        return await angle_deg.get_value()
    return angle_deg


def create_rotational_ij_component_signals(
    i_read: SignalR[float],
    j_read: SignalR[float],
    i_write: Movable[float],
    j_write: Movable[float],
    angle_deg: float | SignalR[float],
    clockwise_frame: bool = True,
) -> tuple[SignalRW[float], SignalRW[float]]:
    """Create virtual i/j signals representing a Cartesian coordinate frame
    that is rotated by a given angle relative to the underlying equipment axes.

    The returned signals expose the position of the system in a *rotated frame
    of reference* (e.g. the sample or stage frame), while transparently mapping
    reads and writes onto the real i/j signals in the fixed equipment (lab) frame.

    From the user's point of view, i and j behave like ordinary orthogonal
    Cartesian axes attached to the rotating object. Internally, all reads apply
    a rotation to the real motor positions, and all writes apply the inverse
    rotation so that the requested motion is achieved in the rotated frame.

    Args:
        i_read (SignalR): SignalR representing the i motor readback.
        j_read (SignalR): representing the j motor readback.
        i_write (Movable): object for setting the i position.
        j_write (Movable): object for setting the j position.
        angle_deg (float | SignalR): Rotation angle in degrees.
        clockwise_frame (boolean): If True, the rotated frame is defined using a
            clockwise rotation; otherwise, a counter-clockwise rotation is used.

    Returns:
        tuple[SignalRW[float], SignalRW[float]] Two virtual read/write signals
        corresponding to the rotated i and j components.
    """
    rotate = rotate_clockwise if clockwise_frame else rotate_counter_clockwise
    inverse_rotate = rotate_counter_clockwise if clockwise_frame else rotate_clockwise

    async def _read_rotated() -> tuple[float, float, float]:
        i, j, ang = await asyncio.gather(
            i_read.get_value(),
            j_read.get_value(),
            _get_angle_deg(angle_deg),
        )
        return (*rotate(radians(ang), i, j), ang)

    async def _write_rotated(i_rot: float, j_rot: float, ang: float) -> None:
        i_new, j_new = inverse_rotate(radians(ang), i_rot, j_rot)
        await asyncio.gather(
            maybe_await(i_write.set(i_new)),
            maybe_await(j_write.set(j_new)),
        )

    def _read_i(i: float, j: float, ang: float) -> float:
        return rotate(radians(ang), i, j)[0]

    async def _set_i(value: float) -> None:
        i_rot, j_rot, ang = await _read_rotated()
        await _write_rotated(value, j_rot, ang)

    def _read_j(i: float, j: float, ang: float) -> float:
        return rotate(radians(ang), i, j)[1]

    async def _set_j(value: float) -> None:
        i_rot, j_rot, ang = await _read_rotated()
        await _write_rotated(i_rot, value, ang)

    return (
        derived_signal_rw(_read_i, _set_i, i=i_read, j=j_read, ang=angle_deg),
        derived_signal_rw(_read_j, _set_j, i=i_read, j=j_read, ang=angle_deg),
    )
