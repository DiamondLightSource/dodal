from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.aithre_lasershaping.goniometer import Goniometer
from dodal.devices.aithre_lasershaping.laser_robot import LaserRobot
from dodal.devices.oav.oav_detector import NullZoomController, OAVBeamCentreFile
from dodal.devices.oav.oav_parameters import OAVConfigBeamCentre

ZOOM_PARAMS_FILE = "/dls_sw/i23/software/aithre/aithre_oav.xml"
DISPLAY_CONFIG = "/dls_sw/i23/software/aithre/aithre_display.configuration"

PREFIX = "LA18L"


@device_factory()
def goniometer() -> Goniometer:
    return Goniometer(f"{PREFIX}-MO-LSR-01:", "goniometer")


@device_factory()
def robot() -> LaserRobot:
    return LaserRobot("robot", f"{PREFIX}-MO-ROBOT-01:")


@device_factory()
def oav(params: OAVConfigBeamCentre | None = None) -> OAVBeamCentreFile:
    return OAVBeamCentreFile(
        prefix=f"{PREFIX}-DI-OAV-01:",
        config=params or OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
        name="oav",
        zoom_controller=NullZoomController(),
    )
