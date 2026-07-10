from dodal.devices.motors import (
    _AZIMUTH,
    _POLAR,
    _TILT,
    _X,
    _Y,
    _Z,
    XYZAzimuthTiltPolarStage,
    create_rotational_ij_component_signals,
)


class I05Goniometer(XYZAzimuthTiltPolarStage):
    """Six-physical-axis stage with a standard xyz translational stage and three axis of
    rotation: azimuth, tilt and polar.

    In addition, it defines two virtual translational axes derived signals, `perp` and
    `long`, which form a rotated Cartesian frame within the x-y plane.
        - `long`: Translation along the rotated X-axis.
        - `perp`: Translation along the rotated Y-axis.

    The `perp` and `long` axes are virtual axes derived from the underlying x and y
    motors using a fixed rotation angle (default 50 degrees). Rotation angle corresponds
    to an angle between analyser axis and X-ray beam axis. From the user's point of
    view, these virtual axes behave as ordinary orthogonal Cartesian translation axes
    aligned with the incoming X-ray beam (long) and perpendicular to it (perp),
    while internally coordinating motion of the x (perpendicular to analyser axis) and y
    (along analyser axis) motors.
    """

    def __init__(
        self,
        prefix: str,
        x_infix: str = _X,
        y_infix: str = _Y,
        z_infix: str = _Z,
        azimuth_infix: str = _AZIMUTH,
        tilt_infix: str = _TILT,
        polar_infix: str = _POLAR,
        rotation_angle_deg: float = 50.0,
        name: str = "",
    ):
        self.rotation_angle_deg = rotation_angle_deg

        super().__init__(
            prefix,
            name,
            x_infix=x_infix,
            y_infix=y_infix,
            z_infix=z_infix,
            azimuth_infix=azimuth_infix,
            tilt_infix=tilt_infix,
            polar_infix=polar_infix,
        )

        with self.add_children_as_readables():
            self.perp, self.long = create_rotational_ij_component_signals(
                i_read=self.x.user_readback,
                i_write=self.x,
                j_read=self.y.user_readback,
                j_write=self.y,
                angle_deg=self.rotation_angle_deg,
            )
