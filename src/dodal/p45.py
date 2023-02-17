from ophyd import Component as Cpt
from ophyd import EpicsMotor, MotorBundle
from ophyd.areadetector.base import ADComponent as Cpt
from pydantic import BaseSettings

from dodal.devices.areadetector import AdAravisDetector


# Settings can be customized via environment variables
class Settings(BaseSettings):
    pv_prefix: str = "BL45P"


_settings = Settings()


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


def make_sample_sample(name: str = "sample_stage") -> TomoStageWithStretchAndSkew:
    return TomoStageWithStretchAndSkew(
        name=name, prefix=f"{_settings.pv_prefix}-MO-STAGE-01:"
    )


def make_choppers(name: str = "chopper") -> Choppers:
    return Choppers(name=name, prefix=f"{_settings.pv_prefix}-MO-CHOP-01:")


def make_det(name: str = "det") -> AdAravisDetector:
    return AdAravisDetector(name=name, prefix=f"{_settings.pv_prefix}-EA-MAP-01:")


def make_diff(name: str = "diff") -> AdAravisDetector:
    return AdAravisDetector(name=name, prefix=f"{_settings.pv_prefix}-EA-DIFF-01:")
