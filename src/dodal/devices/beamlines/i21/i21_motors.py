from dodal.devices.motors import (
    _AZIMUTH,
    _TILT,
    _X,
    _Y,
    _Z,
    XYZAzimuthTiltPolarStage,
    create_rotational_ij_component_signals,
)


class XYZAzimuthTiltPolarParallelPerpendicularStage(XYZAzimuthTiltPolarStage):
    """Six-axis stage with a standard xyz stage and three axis of rotation: azimuth,
    tilt and polar. It also exposes two virtual translational axes that are defined in
    frames of reference attached to the sample.

    - `para` and `perp`:
        Parallel and perpendicular translation axes in the sample frame.
        These axes are derived from the lab-frame x and y motors and rotate
        with the polar angle, so that motion along `para` and `perp`
        remains aligned with the sample regardless of its polar rotation.

    Both virtual axes behave as ordinary orthogonal Cartesian translations
    from the user's point of view, while internally coordinating motion of the
    underlying motors to account for the current rotation angles.

    This allows users to position the sample in physically meaningful, sample-aligned
    coordinates without needing to manually compensate for polar rotations.

    Note: I21 currently uses the following PV to variable
    - PV AZIMUTH but calls the variable phi.
    - PV TILT but calls variable chi.
    - PV RZ but calls it th (theta).

    Inheriting from standard motor class until decided if i21 uses standard name
    convention or need to update variables for this class.
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
        polar_infix: str = "RZ",
    ):
        super().__init__(
            prefix=prefix,
            name=name,
            x_infix=x_infix,
            y_infix=y_infix,
            z_infix=z_infix,
            azimuth_infix=azimuth_infix,
            tilt_infix=tilt_infix,
            polar_infix=polar_infix,
        )
        with self.add_children_as_readables():
            self.para, self.perp = create_rotational_ij_component_signals(
                i_read=self.x.user_readback,
                j_read=self.y.user_readback,
                i_write=self.x,
                j_write=self.y,
                angle_deg=self.polar.user_readback,
                clockwise_frame=False,
            )
