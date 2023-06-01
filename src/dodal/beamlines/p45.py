from dodal.devices.areadetector import AdAravisDetector
from dodal.devices.p45 import Choppers, TomoStageWithStretchAndSkew
from dodal.utils import BeamlinePrefix

PREFIX: str = BeamlinePrefix("p45").beamline_prefix


def sample(name: str = "sample_stage") -> TomoStageWithStretchAndSkew:
    return TomoStageWithStretchAndSkew(name=name, prefix=f"{PREFIX}-MO-STAGE-01:")


def choppers(name: str = "chopper") -> Choppers:
    return Choppers(name=name, prefix=f"{PREFIX}-MO-CHOP-01:")


def det(name: str = "det") -> AdAravisDetector:
    return AdAravisDetector(name=name, prefix=f"{PREFIX}-EA-MAP-01:")


def diff(name: str = "diff") -> AdAravisDetector:
    return AdAravisDetector(name=name, prefix=f"{PREFIX}-EA-DIFF-01:")
