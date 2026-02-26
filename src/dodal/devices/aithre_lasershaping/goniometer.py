from typing import Annotated

from ophyd_async.epics.motor import Motor

from dodal.devices.motors import (
    DefaultInfix,
    XYZOmegaStage,
    create_axis_perp_to_rotation,
)


class Goniometer(XYZOmegaStage):
    """The Aithre lab goniometer and the XYZ stage it sits on.

    `x`, `y` and `z` control the axes of the positioner at the base, while `sampy` and
    `sampz` control the positioner of the sample. `omega` is the rotation about the
    x-axis (along the length of the sample holder).

    The `vertical_position` signal refers to the height of the sample from the point of
    view of the OAV and setting this value moves the sample vertically in the OAV plane
    regardless of the current rotation.
    """

    sampy: Annotated[Motor, DefaultInfix("SAMPY")]
    sampz: Annotated[Motor, DefaultInfix("SAMPZ")]

    def __init__(
        self,
        prefix: str,
        name: str = "",
        **motor_infix_overrides,
    ) -> None:
        super().__init__(prefix=prefix, name=name, **motor_infix_overrides)
        with self.add_children_as_readables():
            self.vertical_position = create_axis_perp_to_rotation(
                self.omega, self.sampz, self.sampy
            )
