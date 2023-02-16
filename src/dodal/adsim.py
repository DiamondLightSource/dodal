#
# Devices for the Diamond simulated AreaDetector
#

import socket

from ophyd import Component, EpicsMotor, MotorBundle
from pydantic import BaseSettings

from dodal.devices.areadetector import AdSimDetector


# Settings can be customized via environment variables
class Settings(BaseSettings):
    pv_prefix: str = socket.gethostname().split(".")[0]


_settings = Settings()


class SimStage(MotorBundle):
    """
    ADSIM EPICS motors
    """

    x: EpicsMotor = Component(EpicsMotor, "M1")
    y: EpicsMotor = Component(EpicsMotor, "M2")
    z: EpicsMotor = Component(EpicsMotor, "M3")
    theta: EpicsMotor = Component(EpicsMotor, "M4")
    load: EpicsMotor = Component(EpicsMotor, "M5")


def make_stage(name: str = "sim_motors") -> SimStage:
    return SimStage(name=name, prefix=f"{_settings.pv_prefix}-MO-SIM-01:")


def make_det(name: str = "adsim") -> AdSimDetector:
    return AdSimDetector(name=name, prefix=f"{_settings.pv_prefix}-AD-SIM-01:")
