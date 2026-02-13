import asyncio
import math
from dataclasses import dataclass
from typing import Annotated, ClassVar, get_args, get_origin, get_type_hints

from ophyd_async.core import SignalRW, StandardReadable, derived_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.common.maths import rotate_clockwise, rotate_counter_clockwise

_X, _Y, _Z = "X", "Y", "Z"

_OMEGA = "OMEGA"
_POLAR = "POLAR"
_AZIMUTH = "AZIMUTH"
_TILT = "TILT"


@dataclass(frozen=True)
class DefaultInfix:
    value: str


class MotorGroup(StandardReadable):
    motor_default_infixes: ClassVar[dict[str, str]]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        motor_default_infixes: dict[str, str] = {}
        hints = get_type_hints(cls, include_extras=True)
        for name, hint in hints.items():
            if get_origin(hint) is Annotated:
                base_type, *metadata = get_args(hint)

                if base_type is Motor:
                    for meta in metadata:
                        if isinstance(meta, DefaultInfix):
                            motor_default_infixes[name] = meta.value
                            break
                    else:
                        raise TypeError(f"{cls.__name__}.{name} missing Infix metadata")

        cls.motor_default_infixes = motor_default_infixes

    def __init__(
        self, prefix: str, name: str = "", **motor_infix_overrides: str
    ) -> None:
        """Initialise MotorGroup with default motor infix. Can be overwritten via key
        worded args for the motor you want. For example, if we have motor x and the
        default infix is "X", we can override by providing x="X1".

        MyMotorGroup("MyPrefix:", x="X1").

        An error will be raised if provided an invalid motor name.
        """
        invalid = set(motor_infix_overrides) - set(self.motor_default_infixes)
        if invalid:
            valid = ", ".join(sorted(self.motor_default_infixes))
            bad = ", ".join(sorted(invalid))
            raise TypeError(
                f"{type(self).__name__} got unexpected motor infix override(s): {bad}. "
                f"Valid motor names are: {valid}"
            )

        with self.add_children_as_readables():
            for motor_name, default_infix in self.motor_default_infixes.items():
                infix = motor_infix_overrides.get(motor_name, default_infix)
                setattr(self, motor_name, Motor(prefix + infix))

        super().__init__(name=name)


class Stage(MotorGroup):
    """For these devices, the following co-ordinates are typical but not enforced:
    - z is horizontal & parallel to the direction of beam travel
    - y is vertical and antiparallel to the force of gravity
    - x is the cross product of y🞬z

    Args:
        prefix (str): Common part of the EPICS PV for all motors, including ":".
        name (str, optional): Name of the stage, each child motor will be named
            "{name}-{field_name}".
        *_infix: Infix between the common prefix and the EPICS motor record fields for
            the field.
    """  # noqa D415

    ...


class XThetaStage(Stage):
    x: Annotated[Motor, DefaultInfix(_X)]
    theta: Annotated[Motor, DefaultInfix("THETA")]


class XYStage(Stage):
    """Two-axis stage. Motors x (infix="X") and y (infix="y")."""

    x: Annotated[Motor, DefaultInfix(_X)]
    y: Annotated[Motor, DefaultInfix(_Y)]


class XYZStage(XYStage):
    """Two-axis stage with an x and a y motor."""

    z: Annotated[Motor, DefaultInfix(_Z)]


class XYZOmegaStage(XYZStage):
    omega: Annotated[Motor, DefaultInfix(_OMEGA)]


class XYZAzimuthStage(XYZStage):
    azimuth: Annotated[Motor, DefaultInfix(_AZIMUTH)]


class XYZThetaStage(XYZStage):
    theta: Annotated[Motor, DefaultInfix("THETA")]


class XYZPolarStage(XYZStage):
    polar: Annotated[Motor, DefaultInfix(_POLAR)]


class XYZPolarAzimuthStage(XYZPolarStage):
    azimuth: Annotated[Motor, DefaultInfix(_AZIMUTH)]


class XYZPolarAzimuthTiltStage(XYZPolarAzimuthStage):
    """Six-axis stage with a standard xyz stage and three axis of rotation: polar,
    azimuth and tilt.
    """

    tilt: Annotated[Motor, DefaultInfix(_TILT)]


class XYPhiStage(XYStage):
    """Three-axis stage with a standard xy stage and one axis of rotation: phi."""

    phi: Annotated[Motor, DefaultInfix("PHI")]


class XYPitchStage(XYStage):
    """Three-axis stage with a standard xy stage and one axis of rotation: pitch."""

    pitch: Annotated[Motor, DefaultInfix("PITCH")]


class XYRollStage(XYStage):
    """Three-axis stage with a standard xy stage and one axis of rotation: roll."""

    roll: Annotated[Motor, DefaultInfix("PITCH")]


class XYZPitchYawStage(XYZStage):
    """Five-axis stage with a standard xyz stage and two axes of rotation: pitch and
    yaw.
    """

    pitch: Annotated[Motor, DefaultInfix("PITCH")]
    yaw: Annotated[Motor, DefaultInfix("YAW")]


class XYZPitchYawRollStage(XYZPitchYawStage):
    """Five-axis stage with a standard xyz stage and three axes of rotation: pitch, yaw,
    and roll.
    """

    roll: Annotated[Motor, DefaultInfix("ROLL")]


class XYZOmegaKappaPhiStage(XYZOmegaStage):
    """Six-axis goniometer with a standard xyz stage and three axes of rotation:
    kappa, phi and omega.
    """

    kappa: Annotated[Motor, DefaultInfix("KAPPA")]
    phi: Annotated[Motor, DefaultInfix("PHI")]

    def __init__(self, prefix: str, name: str = "", **infix_overrides):
        super().__init__(prefix, name, **infix_overrides)

        self.vertical_in_lab_space = create_axis_perp_to_rotation(
            self.omega, self.y, self.z
        )


class XYZKappaPhiStage(XYZStage):
    """Six-axis goniometer with a standard xyz stage and two axes of rotation:
    kappa and phi.
    """

    kappa: Annotated[Motor, DefaultInfix("KAPPA")]
    phi: Annotated[Motor, DefaultInfix("PHI")]


class YZStage(Stage):
    """Two-axis stage with an x and a z motor."""

    y: Annotated[Motor, DefaultInfix(_Y)]
    z: Annotated[Motor, DefaultInfix(_Z)]


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
