from pydantic import BaseSettings

from dodal.devices.areadetector import AdAravisDetector
from dodal.devices.p45 import Choppers, TomoStageWithStretchAndSkew


# Settings can be customized via environment variables
class Settings(BaseSettings):
    pv_prefix: str = "BL45P"


_settings = Settings()


def sample_sample(name: str = "sample_stage") -> TomoStageWithStretchAndSkew:
    return TomoStageWithStretchAndSkew(
        name=name, prefix=f"{_settings.pv_prefix}-MO-STAGE-01:"
    )


def choppers(name: str = "chopper") -> Choppers:
    return Choppers(name=name, prefix=f"{_settings.pv_prefix}-MO-CHOP-01:")


def det(name: str = "det") -> AdAravisDetector:
    return AdAravisDetector(name=name, prefix=f"{_settings.pv_prefix}-EA-MAP-01:")


def diff(name: str = "diff") -> AdAravisDetector:
    return AdAravisDetector(name=name, prefix=f"{_settings.pv_prefix}-EA-DIFF-01:")
