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
    return Goniometer(
        f"{PREFIX}-MO-LSR-01:",
        y_infix="SAMPZ",
        z_infix="SAMPY",
        sampy_infix="Y",
        sampz_infix="Z",
    )


@device_factory()
def robot() -> LaserRobot:
    return LaserRobot(f"{PREFIX}-MO-ROBOT-01:")


@device_factory()
def oav(params: OAVConfigBeamCentre | None = None) -> OAVBeamCentreFile:
    config = (
        params
        if params is not None
        else OAVConfigBeamCentre(
            zoom_params_file=ZOOM_PARAMS_FILE, display_config_file=DISPLAY_CONFIG
        )
    )
    return OAVBeamCentreFile(
        prefix=f"{PREFIX}-DI-OAV-01:",
        config=config,
        zoom_controller=NullZoomController(),
        mjpg_x_size_pv="ArraySize0_RBV",
        mjpg_y_size_pv="ArraySize1_RBV",
        x_direction=-1,
        y_direction=-1,
        z_direction=-1,
    )
