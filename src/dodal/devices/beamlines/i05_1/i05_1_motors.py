from ophyd_async.epics.motor import Motor

from dodal.devices.beamlines.i05_shared.rotation_signals import (
    create_rotational_ij_component_signals,
)
from dodal.devices.motors import XYZPolarAzimuthStage


class XYZPolarAzimuthDefocusStage(XYZPolarAzimuthStage):
    """Six-physical-axis stage with a standard xyz stage, 2 axis of rotation: polar,
    azimuth and one extra tranlastional axis defocus.

    This device exposes four virtual translational axes that are defined in frames
    of reference attached to the sample:

    - `hor` and `vert`:
        Horizontal and vertical virtual translation axes of the rotated sample frame.
        These axes are derived from X and Y axes rotated
        with the azimuth angle, so that motion along `hor` and `vert`
        remains aligned with the gravity direction regardless of its azimuthal rotation.

    - `long` and `perp`:
        Longitudinal and perpendicular virtual translation axes in the rotated sample
        frame. These axes are derived from the Z-axis and the
        virtual `hor` axis, and depend on the polar angle.
        Motion along `long` aligned with the analyser axis,
        while `perp` moves perpendicular to it within the polar rotation plane.

    All four virtual axes behave as ordinary orthogonal Cartesian translations
    from the user's point of view, while internally coordinating motion of the
    underlying motors to account for the current rotation angles.

    This allows users to position the sample in physically meaningful, sample-aligned
    coordinates without needing to manually compensate for azimuth or polar rotations.
    """

    def __init__(
        self,
        prefix: str,
        x_infix="SMX",
        y_infix="SMY",
        z_infix="SMZ",
        polar_infix="POL",
        azimuth_infix="AZM",
        defocus_infix="SMDF",
        name="",
    ):
        super().__init__(
            prefix,
            name,
            x_infix=x_infix,
            y_infix=y_infix,
            z_infix=z_infix,
            polar_infix=polar_infix,
            azimuth_infix=azimuth_infix,
        )

        with self.add_children_as_readables():
            self.defocus = Motor(prefix + defocus_infix)
            self.hor, self.vert = create_rotational_ij_component_signals(
                i_read=self.x.user_readback,
                j_read=self.y.user_readback,
                i_write=self.x,
                j_write=self.y,
                angle_deg=self.azimuth.user_readback,
                clockwise_frame=True,
            )
            self.long, self.perp = create_rotational_ij_component_signals(
                i_read=self.z.user_readback,
                i_write=self.z,
                j_read=self.hor,
                j_write=self.hor,
                angle_deg=self.polar.user_readback,
                clockwise_frame=False,
            )
