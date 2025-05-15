from ophyd_async.epics.motor import Motor

from dodal.devices.motors import Axis, FourAxisGonio


class AithreGoniometer(FourAxisGonio):
    """Goniometer and the stages it sits on"""

    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(
            prefix=prefix,
            name=name,
            infix=("NOT_IN_USE", "SAMPY", "SAMPZ", "OMEGA"),
            upward_axis_at_0=Axis.Z,
            upward_axis_at_minus_90=Axis.Y,
        )
        self.stagex = Motor(prefix + "X")
        self.stagey = Motor(prefix + "Y")
        self.stagez = Motor(prefix + "Z")

        self.x = 0  # overwrite the parent x attribute as the PV does not exist here
