from ophyd_async.epics.motor import Motor

from dodal.devices.motors import Stage


class DiffractometerStage(Stage):
    """
    This is the diffractometer stage which contains both detectors,
    it allows for rotations and also sample position. Contains:
    theta, delta, two_theta, sample_position
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        theta_suffix: str = "THETA",
        delta_suffix: str = "DELTA",
        two_theta_suffix: str = "2THETA",
        sample_pos_suffix: str = "SPOS",
    ):
        with self.add_children_as_readables():
            self.theta = Motor(prefix + theta_suffix)
            self.delta = Motor(prefix + delta_suffix)
            self.two_theta = Motor(prefix + two_theta_suffix)
            self.sample_position = Motor(prefix + sample_pos_suffix)

        super().__init__(name=name)


class DiffractometerBase(Stage):
    """
    This is the diffractometer stage which contains both detectors,
    it allows for translation about x and y and also sample position. Contains:
    x1, x2, y1, y2, y3. Used for aligning the detector to the beam/sample
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        x1_suffix: str = "X1",
        x2_suffix: str = "X2",
        y1_suffix: str = "Y1",
        y2_suffix: str = "Y2",
        y3_suffix: str = "Y3",
    ):
        with self.add_children_as_readables():
            self.x1 = Motor(prefix + x1_suffix)
            self.x2 = Motor(prefix + x2_suffix)
            self.y1 = Motor(prefix + y1_suffix)
            self.y2 = Motor(prefix + y2_suffix)
            self.y3 = Motor(prefix + y3_suffix)

        super().__init__(name=name)
