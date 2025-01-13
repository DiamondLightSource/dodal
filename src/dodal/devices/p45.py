from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class SampleY(StandardReadable):
    """
    Motors for controlling the sample's y position and stretch in the y axis.
    """

    base = Motor("CS:Y")
    stretch = Motor("CS:Y:STRETCH")
    top = Motor("Y:TOP")
    bottom = Motor("Y:BOT")


class SampleTheta(StandardReadable):
    """
    Motors for controlling the sample's theta position and skew
    """

    base = Motor("THETA:POS")
    skew = Motor("THETA:SKEW")
    top = Motor("THETA:TOP")
    bottom = Motor("THETA:BOT")


class TomoStageWithStretchAndSkew(StandardReadable):
    """
    Grouping of motors for the P45 tomography stage
    """

    x = Motor("X")
    y = SampleY("")
    theta = SampleTheta("")


class Choppers(StandardReadable):
    """
    Grouping for the P45 chopper motors
    """

    x = Motor("ENDAT")
    y = Motor("BISS")
