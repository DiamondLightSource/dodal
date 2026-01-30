from ophyd_async.epics.motor import Motor

from dodal.devices.i05.i05_motors import (
    create_rotational_ij_component_signals,
    create_rotational_ij_component_signals_with_motors,
)
from dodal.devices.motors import XYZPolarAzimuthStage


class XYZPolarAzimuthDefocusStage(XYZPolarAzimuthStage):
    """
    Six-axis stage with a standard xyz stage and three axis of rotation: polar, azimuth
    and defocus.
    """

    def __init__(
        self,
        prefix: str,
        x_infix="SMX",
        y_infix="SMY",
        z_infix="SMZ",
        polar_infix="POL",
        azimuth_infix="AZM",
        defocus_infix="SDMF",
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
            self.hor, self.vert = create_rotational_ij_component_signals_with_motors(
                i=self.x,
                j=self.y,
                angle_deg=self.azimuth.user_readback,
            )
            self.perp, _ = create_rotational_ij_component_signals(
                i_read=self.hor,
                i_write=self.hor,
                j_read=self.z.user_readback,
                j_write=self.z,  # type: ignore
                angle_deg=self.azimuth.user_readback,
            )
            self.long, _ = create_rotational_ij_component_signals_with_motors(
                i=self.x,
                j=self.y,
                angle_deg=self.polar.user_readback,
            )
