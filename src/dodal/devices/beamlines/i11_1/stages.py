from ophyd_async.epics.motor import Motor

from dodal.devices.motors import Stage


class LargeStage1(Stage):
    """This is the diffractometer stage specific to i11-1. It could be considered an
    extention of an XZPitchRoll stage with additional signals for Y1, Y2
    YRoll and YLift.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        roll_suffix: str = "ROLL",
        pitch_suffix: str = "PITCH",
        x_suffix: str = "X",
        z_suffix: str = "Z",
        y1_suffix: str = "Y1",
        y2_suffix: str = "Y2",
        y_rotation_suffix: str = "YROT",
    ):
        with self.add_children_as_readables():
            self.y_rot = Motor(prefix + y_rotation_suffix)
            self.roll = Motor(prefix + roll_suffix)
            self.pitch = Motor(prefix + pitch_suffix)

            self.x = Motor(prefix + x_suffix)
            self.y1 = Motor(prefix + y1_suffix)
            self.y2 = Motor(prefix + y2_suffix)
            self.z = Motor(prefix + z_suffix)

        super().__init__(name=name)
