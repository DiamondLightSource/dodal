from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class SampleY(StandardReadable):
    """
    Motors for controlling the sample's y position and stretch in the y axis.
    """

    def __init__(self, prefix: str, name="") -> None:
        self.base = Motor("CS:Y")
        self.stretch = Motor("CS:Y:STRETCH")
        self.top = Motor("Y:TOP")
        self.bottom = Motor("Y:BOT")
        super().__init__(name=name)


class SampleTheta(StandardReadable):
    """
    Motors for controlling the sample's theta position and skew
    """

    def __init__(self, prefix: str, name="") -> None:
        self.base = Motor("THETA:POS")
        self.skew = Motor("THETA:SKEW")
        self.top = Motor("THETA:TOP")
        self.bottom = Motor("THETA:BOT")
        super().__init__(name=name)


class TomoStageWithStretchAndSkew(StandardReadable):
    """
    Grouping of motors for the P45 tomography stage
    """

    def __init__(self, prefix: str, name="") -> None:
        self.x = Motor("X")
        self.y = SampleY("")
        self.theta = SampleTheta("")
        super().__init__(name=name)


class Choppers(StandardReadable):
    """
    Grouping for the P45 chopper motors
    """

    def __init__(self, prefix: str, name="") -> None:
        self.x = Motor("ENDAT")
        self.y = Motor("BISS")
        super().__init__(name=name)
