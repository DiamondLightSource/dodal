from ophyd import Component as Cpt
from ophyd import EpicsMotor, MotorBundle
from ophyd.areadetector.base import ADComponent as Cpt


class SampleY(MotorBundle):
    """
    Motors for controlling the sample's y position and stretch in the y axis.
    """

    base: EpicsMotor = Cpt(EpicsMotor, "CS:Y")
    stretch: EpicsMotor = Cpt(EpicsMotor, "CS:Y:STRETCH")
    top: EpicsMotor = Cpt(EpicsMotor, "Y:TOP")
    bottom: EpicsMotor = Cpt(EpicsMotor, "Y:BOT")


class SampleTheta(MotorBundle):
    """
    Motors for controlling the sample's theta position and skew
    """

    base: EpicsMotor = Cpt(EpicsMotor, "THETA:POS")
    skew: EpicsMotor = Cpt(EpicsMotor, "THETA:SKEW")
    top: EpicsMotor = Cpt(EpicsMotor, "THETA:TOP")
    bottom: EpicsMotor = Cpt(EpicsMotor, "THETA:BOT")


class TomoStageWithStretchAndSkew(MotorBundle):
    """
    Grouping of motors for the P45 tomography stage
    """

    x: EpicsMotor = Cpt(EpicsMotor, "X")
    y: SampleY = Cpt(SampleY, "")
    theta: SampleTheta = Cpt(SampleTheta, "")


class Choppers(MotorBundle):
    """
    Grouping for the P45 chopper motors
    """

    x: EpicsMotor = Cpt(EpicsMotor, "ENDAT")
    y: EpicsMotor = Cpt(EpicsMotor, "BISS")
