from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class SampleY(StandardReadable):
    """
    Motors for controlling the sample's y position and stretch in the y axis.
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.base = Motor(prefix + "CS:Y")
            self.stretch = Motor(prefix + "CS:Y:STRETCH")
            self.top = Motor(prefix + "Y:TOP")
            self.bottom = Motor(prefix + "Y:BOT")
        super().__init__(name)


class SampleTheta(StandardReadable):
    """
    Motors for controlling the sample's theta position and skew
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.base = Motor(prefix + "THETA:POS")
            self.skew = Motor(prefix + "THETA:SKEW")
            self.top = Motor(prefix + "THETA:TOP")
            self.bottom = Motor(prefix + "THETA:BOT")
        super().__init__(name)


class TomoStageWithStretchAndSkew(StandardReadable):
    """
    Grouping of motors for the P45 tomography stage
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")
            self.y = SampleY(prefix)
            self.theta = SampleTheta(prefix)
        super().__init__(name)


class Choppers(StandardReadable):
    """
    Grouping for the P45 chopper motors
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x = Motor(prefix + "ENDAT")
            self.y = Motor(prefix + "BISS")
        super().__init__(name)
