from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorSquad,
)
from dodal.devices.beamlines.i19.access_controlled.blueapi_device import HutchState
from dodal.devices.beamlines.i19.access_controlled.shutter import (
    AccessControlledShutter,
    HutchState,
)
from dodal.devices.beamlines.i19.beamstop import BeamStop
from dodal.devices.beamlines.i19.pin_tip import PinTipCentreHolder
from dodal.devices.oav.oav_detector import OAVBeamCentreFile
from dodal.devices.oav.oav_parameters import OAVConfigBeamCentre
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

# NOTE All PVs for both hutches and the optics have the prefix BL19I
BL = get_beamline_name("i19_1")
PREFIX = BeamlinePrefix("i19", "I")
set_log_beamline(BL)
set_utils_beamline(BL)


I19_1_COMMISSIONING_INSTR_SESSION: str = "cm40638-5"

I19_1_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_PILATUS=1),
    sources=ZebraSources(),
)

ZOOM_PARAMS_FILE = "/dls_sw/i19-1/software/bluesky/jCameraManZoomLevels.xml"
DISPLAY_CONFIG = "/dls_sw/i19-1/software/bluesky/display.configuration"


@device_factory()
def attenuator_motor_squad() -> AttenuatorMotorSquad:
    return AttenuatorMotorSquad(
        hutch=HutchState.EH1, instrument_session=I19_1_COMMISSIONING_INSTR_SESSION
    )


# Needs to wait until enum is fixed on the beamline
# See https://github.com/DiamondLightSource/dodal/issues/1150
@device_factory()
def beamstop() -> BeamStop:
    """Get the i19-1 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-1, it will return the existing object.
    """
    return BeamStop(prefix=f"{PREFIX.beamline_prefix}-RS-ABSB-01:")


@device_factory()
def oav1() -> OAVBeamCentreFile:
    """Get the i19-1 OAV1 device, instantiate it if it hasn't already been.
    The OAV1 camera is placed next to the beampipe along with the Zoom lens."""
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-EA-OAV-01:",
        config=OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@device_factory()
def oav2() -> OAVBeamCentreFile:
    """Get the i19-1 OAV2 device, instantiate it if it hasn't already been.
    The OAV2 camera is places diagonally to the sample and has no FZoom."""
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-EA-OAV-02:",
        config=OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@device_factory()
def pin_tip_centre1() -> PinTipCentreHolder:
    """I19-1 temporary device to hold the pin tip centre position for OAV1."""
    return PinTipCentreHolder(
        prefix=f"{PREFIX.beamline_prefix}-EA-OAV-01:",
    )


@device_factory()
def pin_tip_centre2() -> PinTipCentreHolder:
    """I19-1 temporary device to hold the pin tip centre position for OAV2."""
    return PinTipCentreHolder(
        prefix=f"{PREFIX.beamline_prefix}-EA-OAV-02:",
    )


@device_factory()
def pin_tip_detection1() -> PinTipDetection:
    """Pin tip detection device for OAV1 camera."""
    return PinTipDetection(f"{PREFIX.beamline_prefix}-EA-OAV-01:")


@device_factory()
def pin_tip_detection2() -> PinTipDetection:
    """Pin tip detection device for OAV2 camera."""
    return PinTipDetection(f"{PREFIX.beamline_prefix}-EA-OAV-02:")


@device_factory()
def shutter() -> AccessControlledShutter:
    """Get the i19-1 hutch shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return AccessControlledShutter(
        prefix=f"{PREFIX.beamline_prefix}-PS-SHTR-01:",
        hutch=HutchState.EH1,
        instrument_session=I19_1_COMMISSIONING_INSTR_SESSION,
    )


@device_factory()
def synchrotron() -> Synchrotron:
    """Get the i19-1 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-1, it will return the existing object.
    """
    return Synchrotron()


# NOTE EH1 uses the Zebra 2 box. While a Zebra 1 box exists and is connected
# on the beamline, it is currently not in use
@device_factory()
def zebra() -> Zebra:
    """Get the i19-1 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i19-1, it will return the existing object.
    """
    return Zebra(
        mapping=I19_1_ZEBRA_MAPPING,
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-02:",
    )
