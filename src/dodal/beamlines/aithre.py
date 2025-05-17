from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.aithre_lasershaping.goniometer import Goniometer
from dodal.devices.aithre_lasershaping.laser_robot import LaserRobot

PREFIX = "LA18L"


@device_factory()
def goniometer() -> Goniometer:
    return Goniometer(f"{PREFIX}-MO-LSR-01:", "goniometer")


@device_factory()
def robot() -> LaserRobot:
    return LaserRobot("robot", f"{PREFIX}-MO-ROBOT-01:")
