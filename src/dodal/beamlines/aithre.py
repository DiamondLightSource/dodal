from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.aithre_lasershaping.goniometer import Goniometer
from dodal.devices.oav.oav_detector_base import OAVBase
from dodal.devices.oav.oav_parameters import OAVConfig
from dodal.devices.robot import BartRobot

ZOOM_PARAMS_FILE = "/dls_sw/i23/software/aithre_oav.xml"
DISPLAY_CONFIG = "/dls_sw/i23/software/aithre_display.configuration"

PREFIX = "LA18L"


@device_factory()
def goniometer() -> Goniometer:
    return Goniometer(f"{PREFIX}-MO-LSR-01:", "goniometer")


@device_factory()
def robot() -> BartRobot:
    return BartRobot(prefix=f"{PREFIX}-MO-ROBOT-01:", name="robot")


@device_factory()
def oav(params: OAVConfig | None = None) -> OAVBase:
    return OAVBase(
        prefix=f"{PREFIX}-DI-OAV-01:",
        config=params or OAVConfig(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
        name="oav",
    )
