import socket

from pydantic import BaseSettings

from dodal.devices.adsim import SimStage
from dodal.devices.areadetector import AdSimDetector


# Settings can be customized via environment variables
class Settings(BaseSettings):
    pv_prefix: str = socket.gethostname().split(".")[0]


_settings = Settings()


def make_stage(name: str = "sim_motors") -> SimStage:
    return SimStage(name=name, prefix=f"{_settings.pv_prefix}-MO-SIM-01:")


def make_det(name: str = "adsim") -> AdSimDetector:
    return AdSimDetector(name=name, prefix=f"{_settings.pv_prefix}-AD-SIM-01:")
