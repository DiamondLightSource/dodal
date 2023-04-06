import os

from dodal.devices.adsim import SimStage
from dodal.devices.areadetector import AdSimDetector

from .utils import get_hostname

# Default prefix to hostname unless overriden with export PREFIX=<prefix>
PREFIX: str = os.environ.get("PREFIX", get_hostname())


def stage(name: str = "sim_motors") -> SimStage:
    return SimStage(name=name, prefix=f"{PREFIX}-MO-SIM-01:")


def det(name: str = "adsim") -> AdSimDetector:
    return AdSimDetector(name=name, prefix=f"{PREFIX}-AD-SIM-01:")
