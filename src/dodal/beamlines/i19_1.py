from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.device_manager import DeviceManager
from dodal.devices.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorSquad,
)
from dodal.devices.i19.access_controlled.blueapi_device import HutchState
from dodal.devices.i19.access_controlled.piezo_control import (
    AccessControlledPiezoActuator,
    FocusingMirrorName,
)
from dodal.devices.i19.access_controlled.shutter import (
    AccessControlledShutter,
)
from dodal.devices.i19.beamstop import BeamStop
from dodal.devices.i19.pin_tip import PinTipCentreHolder
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

devices = DeviceManager()


@devices.factory()
def attenuator_motor_squad() -> AttenuatorMotorSquad:
    return AttenuatorMotorSquad(
        hutch=HutchState.EH1, instrument_session=I19_1_COMMISSIONING_INSTR_SESSION
    )


@devices.factory()
def beamstop() -> BeamStop:
    return BeamStop(prefix=f"{PREFIX.beamline_prefix}-RS-ABSB-01:")


@devices.fixture
def oav_config() -> OAVConfigBeamCentre:
    return OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG)


@devices.factory()
def oav1(oav_config: OAVConfigBeamCentre) -> OAVBeamCentreFile:
    """The OAV1 camera, placed next to the beampipe along with the Zoom lens."""
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-EA-OAV-01:",
        config=oav_config,
    )


@devices.factory()
def oav2(oav_config: OAVConfigBeamCentre) -> OAVBeamCentreFile:
    """The OAV2 camera, placed diagonally to the sample. It has no FZoom."""
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-EA-OAV-02:",
        config=oav_config,
    )


@devices.factory()
def pin_tip_centre1() -> PinTipCentreHolder:
    """I19-1 temporary device to hold the pin tip centre position for OAV1."""
    return PinTipCentreHolder(
        prefix=f"{PREFIX.beamline_prefix}-EA-OAV-01:",
        overlay_channel=8,
    )


@devices.factory()
def pin_tip_centre2() -> PinTipCentreHolder:
    """I19-1 temporary device to hold the pin tip centre position for OAV2."""
    return PinTipCentreHolder(
        prefix=f"{PREFIX.beamline_prefix}-EA-OAV-02:",
        overlay_channel=8,
    )


@devices.factory()
def pin_tip_detection1() -> PinTipDetection:
    """Pin tip detection device for OAV1 camera."""
    return PinTipDetection(f"{PREFIX.beamline_prefix}-EA-OAV-01:")


@devices.factory()
def pin_tip_detection2() -> PinTipDetection:
    """Pin tip detection device for OAV2 camera."""
    return PinTipDetection(f"{PREFIX.beamline_prefix}-EA-OAV-02:")


@devices.factory()
def shutter() -> AccessControlledShutter:
    """Access controlled wrapper for the experiment shutter."""
    return AccessControlledShutter(
        prefix=f"{PREFIX.beamline_prefix}-PS-SHTR-01:",
        hutch=HutchState.EH1,
        instrument_session=I19_1_COMMISSIONING_INSTR_SESSION,
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


# NOTE EH1 uses the Zebra 2 box. While a Zebra 1 box exists and is connected
# on the beamline, it is currently not in use
@devices.factory()
def zebra() -> Zebra:
    return Zebra(
        mapping=I19_1_ZEBRA_MAPPING,
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-02:",
    )


@devices.factory()
def hfm_piezo() -> AccessControlledPiezoActuator:
    """Get the i19-1 access controlled hfm piezo device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return AccessControlledPiezoActuator(
        prefix=f"{PREFIX.beamline_prefix}-OP-HFM-01:",
        mirror_type=FocusingMirrorName.HFM,
        hutch=HutchState.EH1,
        instrument_session=I19_1_COMMISSIONING_INSTR_SESSION,
    )


@devices.factory()
def vfm_piezo() -> AccessControlledPiezoActuator:
    """Get the i19-1 access controlled vfm piezo device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return AccessControlledPiezoActuator(
        prefix=f"{PREFIX.beamline_prefix}-OP-VFM-01:",
        mirror_type=FocusingMirrorName.VFM,
        hutch=HutchState.EH1,
        instrument_session=I19_1_COMMISSIONING_INSTR_SESSION,
    )
