from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.aithre_lasershaping.goniometer import Goniometer
from dodal.devices.oav.oav_detector_base import OAV
from dodal.devices.oav.oav_parameters import OAVConfig
from dodal.devices.robot import BartRobot

ZOOM_PARAMS_FILE = "/home/gmg29649/aithre_oav.xml"  # TO-DO: Rename this probably
DISPLAY_CONFIG = "/home/gmg29649/aithre_display.configuration"  # TO-DO: Make this file

PREFIX = "LA18L"


@device_factory()
def goniometer() -> Goniometer:
    return Goniometer(f"{PREFIX}-MO-LSR-01:", "goniometer")


@device_factory()
def robot() -> BartRobot:
    return BartRobot(prefix=f"{PREFIX}-MO-ROBOT-01:", name="robot")


@device_factory()
def oav(params: OAVConfig | None = None) -> OAV:
    return OAV(
        prefix=f"{PREFIX}-DI-OAV-01:",
        config=params or OAVConfig(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
        name="oav",
    )
