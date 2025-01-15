from ophyd import Component as Cpt
from ophyd import EpicsMotor, MotorBundle
from ophyd.areadetector.base import ADComponent as Cpt


class SampleY(MotorBundle):
    """
    Motors for controlling the sample's y position and stretch in the y axis.
    """

    base = Cpt(EpicsMotor, "CS:Y")
    stretch = Cpt(EpicsMotor, "CS:Y:STRETCH")
    top = Cpt(EpicsMotor, "Y:TOP")
    bottom = Cpt(EpicsMotor, "Y:BOT")


class SampleTheta(MotorBundle):
    """
    Motors for controlling the sample's theta position and skew
    """

    base = Cpt(EpicsMotor, "THETA:POS")
    skew = Cpt(EpicsMotor, "THETA:SKEW")
    top = Cpt(EpicsMotor, "THETA:TOP")
    bottom = Cpt(EpicsMotor, "THETA:BOT")


class TomoStageWithStretchAndSkew(MotorBundle):
    """
    Grouping of motors for the P45 tomography stage
    """

    x = Cpt(EpicsMotor, "X")
    y = Cpt(SampleY, "")
    theta = Cpt(SampleTheta, "")


class Choppers(MotorBundle):
    """
    Grouping for the P45 chopper motors
    """

    x = Cpt(EpicsMotor, "ENDAT")
    y = Cpt(EpicsMotor, "BISS")
