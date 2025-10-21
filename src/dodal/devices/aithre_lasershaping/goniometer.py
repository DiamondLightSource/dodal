from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZOmegaStage, create_axis_perp_to_rotation


class Goniometer(XYZOmegaStage):
    """The Aithre lab goniometer and the XYZ stage it sits on.

    `x`, `y` and `z` control the axes of the positioner at the base, while `sampy` and
    `sampz` control the positioner of the sample. `omega` is the rotation about the
    x-axis (along the length of the sample holder).

    The `vertical_position` signal refers to the height of the sample from the point of
    view of the OAV and setting this value moves the sample vertically in the OAV plane
    regardless of the current rotation.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x_infix: str = "X",
        y_infix: str = "SAMPZ",
        z_infix: str = "SAMPY",
        omega_infix: str = "OMEGA",
        stage_y_infix: str = "Y",
        stage_z_infix: str = "Z"
    ) -> None:
        super().__init__(
            prefix=prefix,
            name=name,
            x_infix=x_infix,
            y_infix=y_infix,
            z_infix=z_infix,
            omega_infix=omega_infix,
        )
        with self.add_children_as_readables():
            self.stage_y = Motor(prefix + stage_y_infix)
            self.stage_z = Motor(prefix + stage_z_infix)
            self.vertical_position = create_axis_perp_to_rotation(
                self.omega, self.z, self.y
            )
